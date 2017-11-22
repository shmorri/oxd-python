import os
import sys
from flask import Blueprint, render_template, request, redirect, session
import oxdpython
import logging

app_login = Blueprint('app_login', __name__)

logger = logging.getLogger(__name__)

this_dir = os.path.dirname(os.path.realpath(__file__))
config_location = os.path.join(this_dir, 'demosite.cfg')

# relative import of oxd-python. Comment out the following 3 lines
# if the library has been installed with setup.py install
oxd_path = os.path.dirname(this_dir)

if oxd_path not in sys.path:
    sys.path.insert(0, oxd_path)


#oxc = oxdpython.Client(config_location)


@app_login.route('/login')
def login():
    oxc = oxdpython.Client(config_location)

    dynamic_registration = oxc.config.get("client", "dynamic_registration")
    connection_type = oxc.config.get("oxd", "connection_type")

    if dynamic_registration == 'true' and connection_type == 'web':
        response = oxc.get_client_token()
        protection_access_token = str(response.access_token)
    else:
        protection_access_token = None

    custom_params = {
            "param1":"value1",
            "param2":"value2"
        }

    if connection_type == 'web':
        auth_url = oxc.get_authorization_url(custom_params=custom_params,
                                             protection_access_token=protection_access_token)
    else:
        auth_url = oxc.get_authorization_url(custom_params=custom_params)

    # delete object
    del oxc

    return redirect(auth_url)


@app_login.route('/userinfo')
def userinfo():
    oxc = oxdpython.Client(config_location)
    code = request.args.get('code')
    state = request.args.get('state')

    dynamic_registration = oxc.config.get("client", "dynamic_registration")
    connection_type = oxc.config.get("oxd", "connection_type")
    if dynamic_registration == 'true' and connection_type == 'web':
        response = oxc.get_client_token()
        protection_access_token = str(response.access_token)
    else:
        protection_access_token = None

    if connection_type == 'web':
        tokens = oxc.get_tokens_by_code(code, state, protection_access_token)

        if oxc.config.get("client", "dynamic_registration") == 'true':
            newtokens = oxc.get_access_token_by_refresh_token(refresh_token=tokens.refresh_token, protection_access_token=protection_access_token)
            access_token = newtokens.access_token
        else:
            access_token = tokens.access_token

        user = oxc.get_user_info(access_token, protection_access_token)

        session['username'] = user.name[0]
        session['usermail'] = user.email[0]

    else:
        tokens = oxc.get_tokens_by_code(code, state)

        if oxc.config.get("client", "dynamic_registration") == 'true':
            newtokens = oxc.get_access_token_by_refresh_token(refresh_token=tokens.refresh_token)
            access_token = newtokens.access_token
        else:
            access_token = tokens.access_token

        user = oxc.get_user_info(access_token)

        session['username'] = user.name[0]
        session['usermail'] = user.email[0]

    # delete object
    del oxc

    return render_template('userinfo.html', userName=session['username'], userEmail=session['usermail'])


@app_login.route('/logout')
def logout():
    oxc = oxdpython.Client(config_location)

    dynamic_registration = oxc.config.get("client", "dynamic_registration")
    connection_type = oxc.config.get("oxd", "connection_type")
    if dynamic_registration == 'true' and connection_type == 'web':
        response = oxc.get_client_token()
        protection_access_token = str(response.access_token)
    else:
        protection_access_token = None

    if connection_type == 'web':
        logout_url = oxc.get_logout_uri(protection_access_token=protection_access_token)
    else:
        logout_url = oxc.get_logout_uri()

    session.clear()

    # delete object
    del oxc
    return redirect(logout_url)
