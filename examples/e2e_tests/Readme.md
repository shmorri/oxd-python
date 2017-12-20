# E2E Tests

This folder contains the test scripts that are used for integration testing of 
oxd-python library. These scripts also provide examples for the use of various
functions.

## Requirements

1. OpenID Provider - Gluu Server or Google or any other OIDC respecting server
2. oxd server - oxd server should be installed locally for localhost based tests
3. Python 2.7 - for oxd-python

## Test Scripts

* `openid_socket.py` - Tests the functions relating to OpenID client like
  dynamic registration, authorization flow, logout over socket communication
  with the oxd-server.
* `openid_https.py` - Tests the functions relating to the OpenID Client over
    https with the oxd-https-extension.
 
### Running the tests

* Edit the host and op_host values in `openid_https.cfg` and `openid_socket.cfg`
  to suite the testing environment.
* Run `python openid_socket.py` for running the commands on oxd-server 
* Run `python openid_https.py` for running the commands on oxd-https-extension
* Run `python openid_<type>.py -v` for verbose output of each command
* Run `python openid_<type>.py -h` for help.
