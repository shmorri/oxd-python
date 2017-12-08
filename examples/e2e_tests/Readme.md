# E2E Tests

This folder contains the test scripts that are used for integration testing of 
oxd-python library. These scripts also provide examples for the use of various
functions.

## Requirements

1. OpenID Provider - Gluu Server or Google or any other OIDC respecting server
2. oxd server - oxd server should be installed locally for localhost based tests
3. Python 2.7 - for oxd-python

## Test Scripts

* `openid_commands.py` - Tests the functions relating to OpenID client like
  dynamic registration, authorization flow, logout.
* This script can be used to test both oxd-server via socket communication and
  oxd-https-extension via HTTP.
* Edit the host and op_host values in `openid_https.cfg` and `openid_socket.cfg`
  to suite the testing environment.
* Run `python openid_commands.py socket` for running the commands on oxd-server 
* Run `python openid_commands.py https` for running the commands on oxd-https-extension
* Run `python openid_commands.py <backend> -v` for verbose output of each command
* Run `python openid_commands.py -h` for help.
