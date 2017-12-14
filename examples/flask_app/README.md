# oxd Python Demo site

This is a demo site for oxd-python written using Python Flask to demonstrate how
to use oxd-python to perform authorization with an OpenID Provider and fetch information.

## Deployment

### Prerequisites

1. **Client Server**

    * Python 2.7 with pip installed
    * oxd-server running in the background. [Install oxd server](https://gluu.org/docs/oxd/install/)

2. **OpenID Provider**

     * An OpenID provider like Gluu Server. [Install Gluu Server](https://gluu.org/docs/ce/3.1.1/)

### Testing OpenID Connect with the demo site

* Install oxd-python in the **Client server**

```bash
git clone https://github.com/GluuFederation/oxd-python.git
cd oxd-python
python setup.py install
```

* Switch to the demosite folder

```bash
cd examples/flask_app
```

* Edit the `demosite.cfg` file. Enter the value of `op_host` to point to the OpenID Provider. This can be 
  skipped if you have configured `op_host` when installing oxd-server.
  
* Edit `/etc/hosts` to point `client.example.com` to point to your server.

* Run the demo server

```bash
pip install flask
python demosite.py
```

Now the demosite can be accessed at [https://client.example.com:8080](https://client.example.com:8080)

