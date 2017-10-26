import os
import sys
from flask import Flask, render_template, request, redirect, session
from flask_sslify import SSLify
from Login import app_login
from Uma import app_uma
import oxdpython
import logging


logger = logging.getLogger(__name__)

this_dir = os.path.dirname(os.path.realpath(__file__))
config_location = os.path.join(this_dir, 'demosite.cfg')

# relative import of oxd-python. Comment out the following 3 lines
# if the library has been installed with setup.py install
oxd_path = os.path.dirname(this_dir)

if oxd_path not in sys.path:
    sys.path.insert(0, oxd_path)

app = Flask(__name__)
sslify = SSLify(app)
app.secret_key = 'GluuCentroxy'

app.register_blueprint(app_login)
app.register_blueprint(app_uma)

#oxc = oxdpython.Client(config_location)


@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/setupClient', methods=['GET', 'POST'])
def setupClient():
    oxc = oxdpython.Client(config_location)
    if request.method == 'GET':
        values = oxc.get_config_value()
        if values:
            #oxd_id present
            msg = 'Client already registered'
        else:
            msg = 'Enter data to register'
        return render_template("index.html", op_host=values["op_host"], client_name=values["client_name"], authorization_redirect_uri=values["authorization_redirect_url"],
                               post_logout_uri=values["post_logout_redirect_uri"], conn_value=values["connection_type_value"], oxd_id=values["id"], clientId=values["client_id"],
                               clientSecret=values["client_secret"], conn_type=values["connection_type"], msg=msg, dynamic_registration=values["dynamic_registration"])

    op_host = request.form['ophost']
    client_name = request.form['client_name']
    authorization_redirect_uri = request.form['redirect_uri']
    post_logout_uri = request.form['post_logout_uri']
    conn_type = request.form['conn_type_radio']
    conn_type_value = request.form['conn_type_name']

    try:
        client_id = request.form['ClientId']
        client_secret = request.form['ClientSecret']
    except:
        client_id = ''
        client_secret = ''

    ophost_type = oxc.openid_type(op_host)

    if not ophost_type and client_id == '':
        oxc.config.set("client", "dynamic_registration", "false")
        return render_template("index.html", op_host=op_host, client_name=client_name, authorization_redirect_uri=authorization_redirect_uri,
                               post_logout_uri=post_logout_uri, conn_value=conn_type_value, oxd_id='',
                               msg='Enter clientID and clientSecret', conn_type=conn_type)
    if ophost_type:
        oxc.config.set("client", "dynamic_registration", "true")

    dynamic_registration = oxc.config.get("client", "dynamic_registration")
    client_data = oxc.setup_client(op_host=str(op_host), authorization_redirect_uri=str(authorization_redirect_uri), conn_type=str(conn_type),
                                   conn_type_value=str(conn_type_value), client_name=str(client_name), post_logout_uri=str(post_logout_uri),
                                   client_id=str(client_id), client_secret=str(client_secret))

    oxd_id = client_data.oxd_id
    msg = "Client Set up completed successfully"

    client_id = client_data.client_id
    client_secret = client_data.client_secret

    # delete object
    del oxc

    return render_template("index.html", op_host=op_host, client_name=client_name, authorization_redirect_uri=authorization_redirect_uri,
                           post_logout_uri=post_logout_uri, conn_value=conn_type_value, oxd_id=oxd_id,
                           clientId=client_id, clientSecret=client_secret, msg=msg, conn_type=conn_type, dynamic_registration=dynamic_registration)



@app.route('/update', methods=['GET', 'POST'])
def update():
    oxc = oxdpython.Client(config_location)
    if request.method == 'GET':
        values = oxc.get_config_value()
        return render_template('index.html', op_host=values["op_host"], client_name=values["client_name"], authorization_redirect_uri=values["authorization_redirect_url"],
                               post_logout_uri=values["post_logout_redirect_uri"], conn_value=values["connection_type_value"], oxd_id=values["id"], msg='click on edit to change', dynamic_registration=values["dynamic_registration"])

    conn_type = request.form['conn_type_radio']
    conn_type_value = request.form['conn_type_name']

    oxc.config.set("oxd", "connection_type_value", conn_type_value)

    try:
        client_id = request.form['ClientId']
        client_secret = request.form['ClientSecret']
    except:
        client_id = oxc.config.get("client", "client_id")
        client_secret = oxc.config.get("client", "client_secret")

    dynamic_registration = oxc.config.get("client", "dynamic_registration")

    if dynamic_registration == 'true':

        redirect_uri = request.form['redirect_uri']
        client_name = request.form['client_name']
        post_logout_uri = request.form['post_logout_uri']

        response = oxc.get_client_token()
        protection_access_token = response.access_token
        status = oxc.update_site_registration(client_name=str(client_name), authorization_redirect_uri=str(redirect_uri), post_logout_uri=str(post_logout_uri),
                                              connection_type_value=str(conn_type_value), connection_type=str(conn_type), protection_access_token=str(protection_access_token))
    else:
        oxc.config.set("oxd", "connection_type", conn_type)
        oxc.config.set("oxd", "connection_type_value", conn_type_value)
        oxc.config.set("client", "client_id", client_id)
        oxc.config.set("client", "client_secret", client_secret)
        status = "ok"

    values = oxc.get_config_value()
    if status == "ok":
        msg = 'Client updated successfully'
    else:
        msg = 'update failure'

    # delete object
    del oxc

    return render_template("index.html", op_host=values["op_host"], client_name=values["client_name"], authorization_redirect_uri=values["authorization_redirect_url"],
                          post_logout_uri=values["post_logout_redirect_uri"], conn_value=values["connection_type_value"], oxd_id=values["id"], clientId=values["client_id"],
                           clientSecret=values["client_secret"], conn_type=values["connection_type"], msg=msg, dynamic_registration=values["dynamic_registration"])


@app.route('/delete')
def delete():
    oxc = oxdpython.Client(config_location)
    oxc.delete_config()
    values = oxc.get_config_value()
    if values["op_host"]:
        msg = 'delete failure'
    else:
        msg = 'Client deleted successfully'

    # delete object
    del oxc

    return render_template("index.html", op_host=values["op_host"], client_name=values["client_name"], authorization_redirect_uri=values["authorization_redirect_url"], post_logout_uri=values["post_logout_redirect_uri"], port=values["connection_type_value"], oxd_id=values["id"], msg=msg)


if __name__ == "__main__":
    app.run('127.0.0.1', debug=True, port=8080, ssl_context=('cert/demosite.crt','cert/demosite.key'))
