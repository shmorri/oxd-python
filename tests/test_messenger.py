import socket
import pytest

from mock import patch

from oxdpython.messenger import Messenger


def test_messenger_constructor():
    # port assignment
    mes1 = Messenger()
    assert mes1.port == 8099

    mes2 = Messenger(3000)
    assert mes2.port == 3000

    # host assignment
    assert mes1.host, 'localhost'
    assert mes2.host, 'localhost'

    # socket family and type
    assert isinstance(mes1.sock, socket.SocketType)
    assert mes1.sock.type == socket.SOCK_STREAM
    assert mes1.sock.family == socket.AF_INET

    assert isinstance(mes2.sock, socket.SocketType)
    assert mes2.sock.type == socket.SOCK_STREAM
    assert mes2.sock.family == socket.AF_INET


@patch('socket.socket')
def test_send(mock_socket):
    """Messenger.send sends message"""
    mock_socket.return_value.send.return_value = 5
    mock_socket.return_value.recv.return_value = '0008{"id":5}'

    msgr = Messenger(8099)
    assert msgr.send({"command": "test"}) == {"id": 5}


def test_send_fail():
    """Messenger.send raises error for non connected port"""
    # should raise error when oxd server is not running
    msgr = Messenger(4000)
    with pytest.raises(socket.error):
        msgr.send({'command': 'raise_error'})


@patch('socket.socket')
def test_first_connection(mock_socket):
    """Messenger connects deferred until first send"""
    mock_socket.return_value.send.return_value = 5
    mock_socket.return_value.recv.return_value = '0008{"id":5}'

    msgr = Messenger()
    assert not msgr.firstDone
    msgr.send({})
    assert msgr.firstDone

@patch('socket.socket')
def test_request(mock_socket):
    mock_socket.return_value.send.return_value = 5
    mock_socket.return_value.recv.return_value = '0008{"id":5}'

    msgr = Messenger()
    assert msgr.request('get_user_info') == {"id": 5}


