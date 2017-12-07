#!/usr/bin/python

import cgi
import os
import oxdpython
import traceback

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

envs = os.environ
session = get_session(envs)
message = 'Error: no content returned'

try:
    # get the token after authorization
    f = cgi.FieldStorage()
    try:
        param1 = f.getvalue('param1')
        log("param1=%s" % param1)
    except:
            log("param1 not found")

        # CALL API
        result = "hello world"
        message = result
        log("Got Result from API" % result)
    except:
        logException("Error calling API:\n" + traceback.format_exc())

    d = {}
    d['title'] = TITLE
    d['message'] = message

    print "Content-type: text/html"
    print
    print html % d
