#!/usr/bin/python

import Cookie
import os
import oxdpython
import traceback

from oxdpython.exceptions import NeedInfoError

from constants import *
from appLog import *

client = oxdpython.Client(CONFIG_FILE)

c = Cookie.SimpleCookie()
if 'HTTP_COOKIE' in os.environ:
    c.load(os.environ['HTTP_COOKIE'])

try:
    ticket = c['ticket']
    rpt = client.uma_rp_get_rpt(ticket=ticket)

    c['token_type'] = rpt['token_type']
    c['access_token'] = rpt['access_token']
    log("Writing cookie: \n%s" % str(c))
    print c.output()

    log("Redirecting to request-resource.cgi")
    print "Location: /cgi-bin/request-resource.cgi\r\n"
except NeedInfoError as ne:
    if 'redirect_user' in ne.details:
        claims_url = client.uma_rp_get_claims_gathering_url(ne.details['ticket'])
        print "Location: %s\r\n" % claims_url
    else:
        log("Received NeedInfo Error, but no redirect flag present.")
        logException(traceback.format_exc())
except:
    print "Cannot get RPT"
    log("Failed to get RPT")
    logException(traceback.format_exc())

print "Connection: close \r\n"
print ""
print "Redirecting"




