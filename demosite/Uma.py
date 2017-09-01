import os
import sys
from flask import Blueprint, render_template, request, redirect, session
import oxdpython
import logging

app_uma = Blueprint('app_uma', __name__)

logger = logging.getLogger(__name__)

this_dir = os.path.dirname(os.path.realpath(__file__))
config_location = os.path.join(this_dir, 'demosite.cfg')

# relative import of oxd-python. Comment out the following 3 lines
# if the library has been installed with setup.py install
oxd_path = os.path.dirname(this_dir)

if oxd_path not in sys.path:
    sys.path.insert(0, oxd_path)


#oxc = oxdpython.Client(config_location)


@app_uma.route('/uma')
def uma():
    return render_template('uma_test.html')


@app_uma.route('/protect')
def protect():
    oxc = oxdpython.Client(config_location)
    response = oxc.get_client_token()
    protection_access_token = response.access_token

    resources = [
        {"path": "/photo",
         "conditions": [
             {
                 "scopes":["sobhan_uma_scope"],
                 "ticketScopes":["sobhan_uma_scope"],
                 "httpMethods":["GET"]
             }
         ]
        }
    ]

    result = oxc.uma_rs_protect(protection_access_token, resources)

    # delete object
    del oxc

    return render_template('uma_test.html', msg=result)


@app_uma.route('/check_access', methods=['GET', 'POST'])
def check_access():
    oxc = oxdpython.Client(config_location)
    response = oxc.get_client_token()
    protection_access_token = response.access_token
    rpt = request.form['rpt']
    path = '/photo'
    http_method = 'GET'
    result = oxc.uma_rs_check_access(protection_access_token, rpt, path, http_method)
    ticket = result.ticket

    #This is just for work around purpose. Original fix needs to be worked on.
    for i in result._fields:
        if 'hyphen' in i:
            newkey = i.replace('hyphen', '-')

    wwwauthenticate_header = getattr(result, "wwwhyphenauthenticate_header")

    decodeResponse = str(result)
    decodeResponse = decodeResponse.replace('hyphen', '-')

    # delete object
    del oxc

    return render_template('uma_test.html', ticket=ticket, rpt=rpt, msg=decodeResponse)

def decodeHyphen(str):
    """TO-DO: This is just for work around purpose. Original fix needs to be worked on."""
    newStr = str.replace('hyphen', '-')
    return newStr

@app_uma.route('/get_rpt', methods=['GET', 'POST'])
def getrpt():
    oxc = oxdpython.Client(config_location)
    response = oxc.get_client_token()
    protection_access_token = response.access_token
    ticket = request.form['ticket']
    result = oxc.uma_rp_get_rpt(protection_access_token=protection_access_token, ticket=ticket, scope='sobhan_uma_scope')
    rpt = result.access_token

    # delete object
    del oxc

    return render_template('uma_test.html', ticket=ticket, rpt=rpt, msg=result)


@app_uma.route('/claims_gathering_url', methods=['GET', 'POST'])
def gather():
    oxc = oxdpython.Client(config_location)
    response = oxc.get_client_token()
    protection_access_token = response.access_token
    ticket = request.form['ticket']
    result = oxc.uma_rp_get_claims_gathering_url(protection_access_token=protection_access_token, claims_redirect_uri="https://client.example.com:8080", ticket=ticket)

    # delete object
    del oxc

    return render_template('uma_test.html', ticket=ticket, msg=result)
