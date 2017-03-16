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

## Deployment Instructions

1. Make sure you have oxd installed and running.
2. Edit *demosite.cfg* and update *hostname* with your local web 
server's hostname. This file is used by oxd-python to register your
client.
3. Edit *constants.py* and check the filesystem paths to make sure 
they are ok, and are writeable by the web server.
4. sftp all the files to your cgi-bin
5. Run `./setupDemo.py` to initialize the database
6. Navigate to https://hostname/home.cgi and click on login.
7. If something goes wrong, check the logs.

See the sequence diagram below to get a better picture of the flow of 
this application.

![Demo Sequence Diagram](https://raw.githubusercontent.com/GluuFederation/oxd-python/master/demo-cgi/sequence_diagram.png)
