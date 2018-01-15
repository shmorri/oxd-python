## Demo CGI

CGI scripts are the simplest possible Web applications. The goal of
these scripts is to show oxd-python at work with a minimal amount of
application overhead. A cookie is used to track a session id, which
is persisted using the simple python shelve database interface.

This sample consists of the following files

* **demosite.cfg** This file contains the callback urls and other site
specific settings
* **home.cgi** This is the main page of the app. Navigate to this page
first.
* **redirect-to-login.cgi** This script redirects the user to the
OpenID Connect login (if no sessioin exists) and authorization pages.
* **callback-login.cgi** This script uses the authorization code to
obtain user information, and create a session.
* **redirect-to-logout.cgi** This script sends the person to the
OpenID Connect logout page.
* **callback-logout.cgi** This page is called for OpenID Connect
front channel logout. It clears the session and cookie, and redirects
to the logout confirmation page
* **logout-confirmation.cgi** This pages checks to make sure that the
cookie and DB session are removed.
* **setupDemo.py** Helper script used to create the DB and set
file permissions.
* **appLog.py** Module to centralize logging code
* **constants.py** Module to centralize constant values
* **request-resource.cgi** Script that requests data from UMA Resource Server
* **get-rpt.cgi** Script that gets the RPT token from the Auth Server
* **callback-claims.cgi** The script parses the response from Authorization
server and send the ticket to re-fetch RPT on successful authorization

## Deployment of demosite in Ubuntu

1. Install [oxd-server](https://gluu.org/docs/oxd/install/)
2. Edit `/opt/oxd-server/conf/oxd-conf.json` and enter your OXD License details. Edit `/opt/oxd-server/conf/oxd-default-site-conf.json` and enter the value for `op_host` pointing to your Gluu Server installation. Run `service gluu-oxd-server start`
3. Install oxd-python
    ```
    # apt install python-pip
    # pip install oxdpython
    ```
3. Install and configure Apache 2
    ```
    # apt install apache2
    # a2enmod cgi
    # a2enmod ssl
    # a2dissite 000-default
    # a2ensite default-ssl
    ```
2. Clone the demosite and setup for cgi-bin
    ```
    # cd /usr/lib/cgi-bin/
    # git clone https://github.com/GluuFederation/oxd-python.git
    # cp oxd-python/examples/cgi_app/* .
    # chmod +x *.cgi
    ```
3. Edit `COOKIE_DOMAIN` in `constants.py` to suit your domain name.
4. Setup logging and initialize the app
    ```
    # mkdir -p /var/log/sampleapp/
    # python setupDemo.py
    ```
4. Change the domain names in `/var/log/sampleapp/demosite.cfg` URLs to match yours. (Similar to Step 3)
5. Visit `https://your-hostname/cgi-bin/home.cgi`
6. To debug check the logs are `/var/log/sampleapp/app.log` and `/var/log/oxd-server.log`

## UMA Demo

Let us set up the three components required for UMA:
* Authorization Server (AS)  - The Gluu server set as OP host - Already Setup
* Requesting Party (RP) - `viewInventory.cgi` - Already present as a part of this demo app
* Resource Server (RS) - The Flask app inside the `uma_rs` directory - Follow instructions below

### Set up demo UMA Resource Server

1. Open a new terminal window and navigate to the `uma_rs` directory
    ```
    # cd /usr/lib/cgi-bin/oxd-python/examples/cgi_app/uma_rs
    ```
2. Install requirements for the app
    ```
    # pip install flask pyOpenSSL
    ```
3. Edit the config file `rs-oxd.cfg` and input the `op_host` you are using. The `authorization_redirect_uri` 
   is a part of the of the OAuth Spec requirement. You DON'T have to have a resolving URL, you can leave the dummy value
   in place.
4. Run `python app.py` to start the server.
5. Visit `https://<your-hostname>:8085/` to see the setup page. Click Setup. This will register the demo resources in
   the Authorization Server and give you a page containing the details of the resources and their endpoints.

### Seeing UMA RP in action

1. Visit `https://<your-hostname>/cgi-bin/request-resource.cgi`, based on the requirements and configured policies,
the redirects from this script should lead to fetching the resource.

TODO: Configuring policies and asking for more information from users

Browse the code of `viewInventory.cgi` to see how it is working.

