import json
import socket
import logging
import urllib2

from . import __version__

logger = logging.getLogger(__name__)

class Messenger(object):
    """Base class for the different messengers employed by the oxdpython Client
    """
    def __init__(self):
        self._access_token = ''

    @staticmethod
    def create(host='localhost', port='8099', https_extension=False):
        if https_extension:
            return HttpMessenger(host)
        return SocketMessenger(host, port)

    def request(self, command, **kwargs):
        """Mandatory function that should be implemented by the subclasses. The
        Client will call this function with the command and the params to be
        sent to the oxd-server

        Args:
            command (str): The command that has to be sent to the oxd-server
            **kwargs: The parameters that should accompany the request

        Returns:
            dict: the returned response from oxd-server as a dictionary
        """
        pass

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, token):
        if not isinstance(token, str) and not isinstance(token, unicode):
            raise ValueError("Access token should be a string or Unicode. "
                             "Received %s" % type(token))
        self._access_token = token


class SocketMessenger(Messenger):
    """A class which takes care of the socket communication with oxD Server.
    The object is initialized with the port number
    """
    def __init__(self, host='localhost', port=8099):
        """Constructor for SocketMessenger

        Args:
            host (str) - the host to connect for oxd-server, default localhost
            port (integer) - the port number to bind to the host, default
                             is 8099
        """
        Messenger.__init__(self)
        self.host = host
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
            payload["params"][item] = kwargs.get(item)

        if self.access_token:
            payload["params"]["protection_access_token"] = self.access_token

        return self.send(payload)

    def __str__(self):
        return "SocketMessenger(%s, %s)" % (self.host, self.port)


class HttpMessenger(Messenger):
    """HttpMessenger provides the communication channel for oxd-https-extension

    Args:
        host (str): host URL to which the requests are to be made
    """
    def __init__(self, host):
        Messenger.__init__(self)
        self.base = self.__base_url(host)

    def __base_url(self, host):
        if host[-1] != "/":
            host += "/"
        if not host.startswith("https://") and \
                not host.startswith("http://"):
            host = "https://" + host
        return host

    def request(self, command, **kwargs):
        """Function that builds the request and returns the response

        Args:
            command (str): The command that has to be sent to the oxd-server
            **kwargs: The parameters that should accompany the request

        Returns:
            dict: the returned response from oxd-server as a dictionary
        """
        url = self.base + command.replace("_", "-")

        # FIXME This is a temporary fix to mitigate the difference between
        # oxd-server and oxd-https-extension. remove when upstream fix arrives
        if command == 'update_site_registration':
            url = self.base + "update-site"

        req = urllib2.Request(url, json.dumps(kwargs))
        req.add_header("User-Agent", "oxdpython/%s" % __version__)
        req.add_header("Content-type", "application/json; charset=UTF-8")

        # add the protection token if available
        if self.access_token:
            req.add_header("Authorization",
                           "Bearer {0}".format(self.access_token))

        resp = urllib2.urlopen(req)
        return json.load(resp)

    def __str__(self):
        return "HttpMessenger(%s)" % self.base
