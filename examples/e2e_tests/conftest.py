import oxdpython
import pytest

@pytest.fixture(scope="module", params=["openid_https.cfg", "opend_socket.py"])
def c(request):
    return oxdpython.Client(request.param)

@pytest.fixture(scope="module")
def uma_c():
    return oxdpython.Client('uma_client.cfg')
