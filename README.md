# oxd-python
oxD Python is a client library for the [Gluu oxD Server RP](https://www.gluu.org/docs-oxd/).

It is a thin wrapper around the communication protocol of oxD server. This can be used to access the OpenID connect & UMA Authorization end points of the Gluu Server via the oxD RP. This library provides the function calls required by a website to access user information from a OpenID Connect Provider (OP) by using the OxD as the Relying Party (RP).

This page gives an overview of how to use the library. See the [API docs](https://oxd.gluu.org/api-docs/oxd-python/2.4.4) for in-depth information about the various functions and their parameters. The source code is hosted in Github [here](https://github.com/GluuFederation/oxd-python).

## Deployment

### Prerequisites

* Install oxD Server as explained in the [installation docs](https://www.gluu.org/docs-oxd/oxdserver/install/)

### Installation
* Download the zip of the oxD Python Library from [here](https://github.com/GluuFederation/oxd-python/releases) and unzip to your location of choice

```
cd oxdpython-version
python setup.py install
```

### Using the Library in your website

#### Configure the site

Once the library is installed, it can be used by any Python web application deployed on the server. First, create a copy of the sample configuration file for your website in a server *writable* location and edit the configuration. For example

```
cp sample.cfg /var/www/demosite/demosite.cfg
```

**Note:** The website is registered with the OP and its ID is stored in this config file, also are the other peristant information about the website. So the config file needs to be *writable* for the server. The [sample.cfg](https://github.com/GluuFederation/oxd-python/blob/master/sample.cfg) file contains complete documentation about itself.

#### Website Registration

The `Client` class of the library provides all the required methods required for the website to communicate with the oxD RP through sockets.

```python
from oxdpython import Client

config = "/var/www/demosite/demosite.cfg"  # This should be writable by the server
client = Client(config)
client.register_client()
```

**Note:** `register_client()` can be skipped as any `get_authorization_url()` automatically registers the site.

#### Get Authorization URL

Next Generate an authorization url which the user can visit to authorize your application to use the information from the OP.

```python
auth_url = client.get_authorization_url()
```
In the web application, redirect the user for authentication can authorization at the OP.

#### Get access token

After authentication and authorization at the OP, the user is redirected to the website. The website needs to parse the information fromt the callback url and pass it on to get the access token for fetching user information. Refer to your web framework to how to get these values from the callback url.

```python
token = client.get_tokens_by_code(code, scopes, state)
```

#### Get user claims

Claims (information fields) made availble by the OP can be fethed using the access token obtained above.

```python
user = oxc.get_user_info(token)

# The claims can be accessed using the dot notation.
print user.username
print user.inum
print user.website

print user._fields  # to print all the fields

# to check for a particular field and get the information
if 'website' in user._fields:
    print getattr(user, 'website')
    # or
    print user.website
```

#### Logout the user

```python
logout_uri = oxc.get_logout_uri()
```
Redirect the user to this uri from you web application to logout the user.

### Demo Site

To get the complete understanding of how all the functions are used, see the demo site written using Python Flask [here](https://github.com/GluuFederation/oxd-python/blob/master/demosite/demosite.py)


## Contributing to Library

* Fork the project in [Github](https://github.com/GluuFederation/oxd-python).
* [Open Issues](https://github.com/GluuFederation/oxd-python/issues) when you find bugs

