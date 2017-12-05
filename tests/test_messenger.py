import unittest

from mock import patch, MagicMock

from oxdpython.messenger import SocketMessenger

@patch('socket.socket')
class SocketMessengerTestCase(unittest.TestCase):
    def setUp(self):
        self.msgr = SocketMessenger()

    def test_send(self, mock_socket):
        """SocketMessenger.send sends message"""
        mock_socket.return_value.send.return_value = 5
        mock_socket.return_value.recv.return_value = '0008{"id":5}'

        assert self.msgr.send({"command": "test"}) == {"id": 5}

    def test_first_connection(self, mock_socket):
        """SocketMessenger connects deferred until first send"""
        mock_socket.return_value.send.return_value = 5
        mock_socket.return_value.recv.return_value = '0008{"id":5}'

        assert not self.msgr.firstDone
        self.msgr.send({})
        assert self.msgr.firstDone

    def test_request(self, mock_socket):
        mock_socket.return_value.send.return_value = 5
        mock_socket.return_value.recv.return_value = '0008{"id":5}'

        assert self.msgr.request('get_user_info') == {"id": 5}

    def test_request_adds_protection_token(self, mock_socket):
        self.msgr.send = MagicMock()

        self.msgr.access_token = 'test-token'
        self.msgr.request('test_command')

        assert 'protection_access_token' in self.msgr.send.call_args[0][0]["params"]

