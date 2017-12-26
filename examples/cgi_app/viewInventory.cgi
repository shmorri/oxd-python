#!/usr/bin/python

import cgi
import os
import oxdpython
import traceback
import urllib2
import json
import ssl

from constants import *
from appLog import *
from common import *

html = """<HTML><HEAD><TITLE>%(title)s</TITLE></HEAD>
<BODY>
<H1>%(title)s</H1>
%(message)s
<hr>
<h6>POWERED BY</h6>
<IMG SRC="https://www.gluu.org/wp-content/themes/gluu/images/logo.png" alt="Powered by Gluu"
 width="100" />
</BODY>
</HTML>
"""

api_url = RS_BASE_URL + "api/photos/"
TITLE = 'UMA RP Accessing %s' % api_url
envs = os.environ
session = get_session(envs)
client = oxdpython.Client(CONFIG_FILE)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

response = {}
try:
    response = json.load(urllib2.urlopen(api_url, context=ctx))
    message = json.dumps(response)
except:
    message = "Error: no content returned"
    logError("Cannot Open URL %s" % api_url)
    logException(traceback.format_exc())

# First will be rejected as it is without a Bearer Token, if denied
# Get the RPT and use the access_token
if response.get("access") == "denied":
    rpt = client.uma_rp_get_rpt(ticket=response["ticket"])
    try:
        req = urllib2.Request(api_url)
        req.add_header('Authorization', '%s %s' %(rpt['token_type'], rpt['access_token']))
        response = json.load(urllib2.urlopen(api_url, context=ctx))
        message = json.dumps(response)
    except:
        logError("Failed to fetch URL with RPT %s" % rpt)
        logException(traceback.format_exc())

d = {}
d['title'] = TITLE
d['message'] = message

print "Content-type: text/html"
print
print html % d
