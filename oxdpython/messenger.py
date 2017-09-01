import json
import socket
import logging
import urllib2
import ssl


from collections import namedtuple

LOGGER = logging.getLogger(__name__)


class Messenger:
    """A class which takes care of the socket communication with oxd Server.
    The object is initialized with the port number
    """
    def __init__(self, port=8099):
        """Constructor for Messenger

        Args:
            port (integer) - the port number to bind to the localhost, default
                             is 8099
        """
        self.host = 'localhost'
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        LOGGER.debug("Creating a AF_INET, SOCK_STREAM socket.")
        self.firstDone = False



    def __connect(self):
        """A helper function to make connection."""
        try:
            LOGGER.debug("Socket connecting to %s:%s", self.host, self.port)
            self.sock.connect((self.host, self.port))
        except socket.error as e:
            LOGGER.exception("socket error %s", e)
            LOGGER.error("Closing socket and recreating a new one.")
            self.sock.close()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))

    def __json_object_hook(self, d):
        """Function to customize the json.loads to return named tuple instead
        of a dict"""

        #if a response key contains '-' then replace it with 'hyphen'
        d = self.encodeHyphen(d)

        return namedtuple('response', d.keys())(*d.values())

    def __json2obj(self, data):
        """Helper function which converts the json string into a namedtuple
        so the reponse values can be accessed like objects instead of dicts"""
        return json.loads(data, object_hook=self.__json_object_hook)

    def encodeHyphen(self, d):
        """TO-DO: This is just for work around purpose. Original fix needs to be worked on."""
        for i in d.keys():
            if '-' in i:
                newkey = i.replace('-', 'hyphen')
                val = d[i]
                d.pop(i)
                d[newkey] = val
        return d

    def send(self, command):
        """Send function sends the command to the oxd server and recieves the
        response.

        Args:
            command (dict) - Dict representation of the JSON command string

        Returns:
            response (dict) - The JSON response from the oxd Server as a dict
        """
        cmd = json.dumps(command)
        cmd = "{:04d}".format(len(cmd)) + cmd
        msg_length = len(cmd)

        # Makes the first time connection
        if not self.firstDone:
            LOGGER.info('Initiating first time socket connection.')
            self.__connect()
            self.firstDone = True

        # Send the message to the server
        totalsent = 0
        while totalsent < msg_length:
            try:
                LOGGER.debug("Sending: %s", cmd[totalsent:])
                sent = self.sock.send(cmd[totalsent:])
                totalsent = totalsent + sent
            except socket.error as e:
                LOGGER.exception("Reconneting due to socket error. %s", e)
                self.__connect()
                LOGGER.info("Reconnected to socket.")

        # Check and recieve the response if available
        parts = []
        resp_length = 0
        recieved = 0
        done = False
        while not done:
            part = self.sock.recv(1024)
            if part == "":
                LOGGER.error("Socket connection broken, read empty.")
                self.__connect()
                LOGGER.info("Reconnected to socket.")

            # Find out the length of the response
            if len(part) > 0 and resp_length == 0:
                resp_length = int(part[0:4])
                part = part[4:]

            # Set Done flag
            recieved = recieved + len(part)
            if recieved >= resp_length:
                done = True

            parts.append(part)

        response = "".join(parts)
        # return the JSON as a namedtuple object
        return self.__json2obj(response)


    def sendtohttp(self, params, rest_url):
        """send function sends the command to the oxd server and recieves the
        response for web connection type.

        Args:
            params (dict) - Dict representation of the JSON param string
            rest_url - Url of the rest API

        Returns:
            response (dict) - The JSON response from the oxd Server as a dict
        """


        param = json.dumps(params)

        if 'protection_access_token' in param:
            accessToken = 'Bearer ' + params.get('protection_access_token', 'None')
        else:
            accessToken = ''

        headers = {'Content-Type': 'application/json', 'Authorization': accessToken}

        request = urllib2.Request(rest_url, param, headers)
        gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        response = urllib2.urlopen(request, context=gcontext)

        resp_page = response.read()

        response = "".join(resp_page)
        # return the JSON as a namedtuple object
        return self.__json2obj(response)
