# oxd-python
oxD Python is a client library for the Gluu oxD Server. For information about oxD, visit [http://oxd.gluu.org](http://oxd.gluu.org)

## Deployment

### Prerequisites

* Python 2.7
* Gluu oxD Server - [Installation docs](https://www.gluu.org/docs-oxd/oxdserver/install/)

### Installation
* *Official Gluu Repo* - Install using the package manager from the official Gluu repository.

```
apt-get install gluu-oxd-python

# or

yum install gluu-oxd-python
```

* *Source from Github* -  Download the zip of the oxD Python Library from [here](https://github.com/GluuFederation/oxd-python/releases) and unzip to your location of choice

```
cd oxdpython-version
python setup.py install
```

### Next Steps

* Scroll [below](#using-the-library-in-your-website) to learn how to use the library in an application.
* See the [API docs](http://oxd-python.readthedocs.io/en/2.4.4/) for in-depth information about the various functions and their parameters.
* See the code of a [sample Flask app](https://github.com/GluuFederation/oxd-python/blob/master/demosite/demosite.py) built using oxd-python.
* Browse the source code is hosted in Github [here](https://github.com/GluuFederation/oxd-python).

### Using the Library in your website

#### Configure the site

Once the library is installed, it can be used by any Python web application deployed on the server. First, create a copy of the [sample configuration file](https://github.com/GluuFederation/oxd-python/blob/master/sample.cfg) for your website in a server *writable* location and edit the configuration. For example `/var/www/demosite/demosite.cfg`.

**Note:** The website is registered with the OP and its ID is stored in this config file, also are the other peristant information about the website. So the config file needs to be *writable* for the server. The [sample.cfg](https://github.com/GluuFederation/oxd-python/blob/master/sample.cfg) file contains complete documentation about itself.

#### Website Registration

The `Client` class of the library provides all the required methods required for the website to communicate with the oxD RP through sockets.

```python
from oxdpython import Client

config = "/var/www/demosite/demosite.cfg"  # This should be writable by the server
client = Client(config)
client.register_site()
```

**Note:** `register_site()` can be skipped as any `get_authorization_url()` automatically registers the site.

#### Get Authorization URL

Next Generate an authorization url which the user can visit to authorize your application to use the information from the OP.

```python
auth_url = client.get_authorization_url()
```

#### Get access token

In the web application, redirect the user to the `auth_url`. After authentication and authorization at the OP, the user is sent back to the website. The website needs to parse the information from the callback url and use it to get the access token. Refer to your web framework to how to get these values from the callback url.

```python
# code, scopes, state = parse_callback_url_querystring()  # Refer your web framework
tokens = client.get_tokens_by_code(code, scopes, state)
```

#### Get user claims

Claims (information fields) made availble by the OP can be fethed using the access token obtained above.

```python
user = oxc.get_user_info(tokens.access_token)

# The claims can be accessed using the dot notation.
print user.username
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
Redirect the user to this uri from your web application to logout the user.


#### Update Site Registration
Any changes in the configuration of the client can be updated in the OP by using this function call. Look at the [oxD docs](https://oxd.gluu.org/docs/oxdserver/) for the complete list of the configuration values that could be set.

```python
scopes = ','.join(['openid','profile','uma_protection'])  # ensure list is converted to string
client.config.set('client', 'scope', scopes)
client.update_site_registration()
```
