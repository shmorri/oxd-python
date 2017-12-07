# E2E Tests

This folder contains the test scripts that are used for integration testing of 
oxd-python library. These scripts also provide examples for the use of various
functions.

## Requirements

1. OpenID Provider - Gluu Server or Google or any other OIDC respecting server
2. oxd server - oxd server should be installed locally for localhost based tests
3. Python 2.7 - for oxd-python

## Running Tests

Run from outside this directory. 
```bash
pytest e2e_tests
```



## Test Scripts

1. `openid_commands.py` - Tests the functions relating to OpenID client like
    dynamic registration, authorization flow, logout.
