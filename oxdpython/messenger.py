import json
import socket
import logging

from collections import namedtuple

logger = logging.getLogger(__name__)


class Messenger:
    """A class which takes care of the socket communication with oxD Server.
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
        logger.debug("Creating a AF_INET, SOCK_STREAM socket.")
        self.firstDone = False

    def __connect(self):
        """A helper function to make connection."""
        try:
            logger.debug("Socket connecting to %s:%s", self.host, self.port)
            self.sock.connect((self.host, self.port))
        except socket.error as e:
            logger.exception("socket error %s", e)
            logger.error("Closing socket and recreating a new one.")
            self.sock.close()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))

    def send(self, command):
        """send function sends the command to the oxD server and recieves the
        response.

        Args:
            command (dict) - Dict representation of the JSON command string

        Returns:
            response (dict) - The JSON response from the oxD Server as a dict
        """
        cmd = json.dumps(command)
        cmd = "{:04d}".format(len(cmd)) + cmd
        msg_length = len(cmd)

        # make the first time connection
        if not self.firstDone:
            logger.info('Initiating first time socket connection.')
            self.__connect()
            self.firstDone = True

        # Send the message the to the server
        totalsent = 0
        while totalsent < msg_length:
            try:
                logger.debug("Sending: %s", cmd[totalsent:])
                sent = self.sock.send(cmd[totalsent:])
                totalsent = totalsent + sent
            except socket.error as e:
                logger.exception("Reconneting due to socket error. %s", e)
                self.__connect()
                logger.info("Reconnected to socket.")

        # Check and receive the response if available
        parts = []
        resp_length = 0
        received = 0
        done = False
        while not done:
            part = self.sock.recv(1024)
            if part == "":
                logger.error("Socket connection broken, read empty.")
                self.__connect()
                logger.info("Reconnected to socket.")

            # Find out the length of the response
            if len(part) > 0 and resp_length == 0:
                resp_length = int(part[0:4])
                part = part[4:]

            # Set Done flag
            received = received + len(part)
            if received >= resp_length:
                done = True

            parts.append(part)

        response = "".join(parts)
        # return the JSON as a namedtuple object
        return json.loads(response)

    def request(self, command, **kwargs):
        """Function that builds the request and returns the response from
        oxd-server

        Args:
            command (str): The command that has to be sent to the oxd-server
            **kwargs: The parameters that should accompany the request

        Returns:
            dict: the returned response from oxd-server as a dictionary
        """
        payload = {
            "command": command,
            "params": dict()
        }
        for item in kwargs.keys():
            payload['params'][item] = kwargs.get(item)

        return self.send(payload)
