import oxdpython


def test_metadata():
    assert oxdpython.__name__, "oxdpython"
    assert oxdpython.__description__, "A Python Client for oxD Server"
    assert oxdpython.__version__, "3.1.1"
    assert oxdpython.__author__, "Gluu"
