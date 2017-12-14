import unittest

from mock import patch, MagicMock

from oxdpython.messenger import SocketMessenger

class SocketMessengerTestCase(unittest.TestCase):
    def setUp(self):
        self.msgr = SocketMessenger()
        self.msgr.sock = MagicMock()
        self.msgr.sock.send.return_value = 5
        self.msgr.sock.recv.return_value = '0008{"id":5}'

    def test_send(self):
        """SocketMessenger.send sends message"""
        assert self.msgr.send({"command": "test"}) == {"id": 5}

    def test_first_connection(self):
        """SocketMessenger connects deferred until first send"""
        assert not self.msgr.firstDone
        self.msgr.send({})
        assert self.msgr.firstDone

    def test_request(self):
        assert self.msgr.request('get_user_info') == {"id": 5}

    def test_request_adds_protection_token(self):
        self.msgr.send = MagicMock()

        self.msgr.access_token = 'test-token'
        self.msgr.request('test_command')

        assert 'protection_access_token' in self.msgr.send.call_args[0][0]["params"]

