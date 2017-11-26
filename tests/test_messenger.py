import socket
import pytest

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


def test_send():
    """Messenger.send sends message"""
    msgr = Messenger(8099)
    response = msgr.send({"command": "test"})
    assert response.status


def test_send_fail():
    """Messenger.send raises error for non connected port"""
    # should raise error when oxd server is not running
    msgr = Messenger(4000)
    with pytest.raises(socket.error):
        msgr.send({'command': 'raise_error'})


def test_first_connection():
    """Messenger connects deffered until first send"""
    msgr = Messenger()
    assert not msgr.firstDone
    msgr.send({})
    assert msgr.firstDone
