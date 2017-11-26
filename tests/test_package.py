import oxdpython

from nose.tools import assert_equal

def test_metadata():
    assert_equal(oxdpython.__name__, "oxdpython")
    assert_equal(oxdpython.__description__, "A Python Client for oxD Server")
    assert_equal(oxdpython.__version__, "3.0.1")
    assert_equal(oxdpython.__author__, "Gluu")
