import os
import oxdpython
from oxdpython.exceptions import OxdServerError

from flask import Flask, render_template, redirect, request, make_response, url_for, jsonify

app = Flask(__name__)

this_dir = os.path.dirname(os.path.realpath(__file__))
config = os.path.join(this_dir, 'rs.cfg')
oxc = oxdpython.Client(config)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/protect', methods=['POST'])
def protect():
    if not oxc.oxd_id:
        oxc.register_site()

    path = request.form.get('path')
    scope = request.form.get('scope')
    http_method = request.form.get('http_method')

    condition = {}
    if type(http_method) is list:
        condition['httpMethods'] = http_method
    else:
        condition['httpMethods'] = [http_method]

    if type(scope) is list:
        condition['scopes'] = scope
    else:
        condition['scopes'] = [scope]

    resources = [dict(path=path, conditions=[condition])]

    protected = oxc.uma_rs_protect(resources)
    if protected:
        return '<html><body>Protected. <a href="/">Go Home</a></body></html>'
    else:
        return '<html><body>Not protected. <a href="/">Go Home</a></body></html>'


@app.route('/resource/<resource>/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def access_resource(resource):
    rpt = request.headers.get('Authorization')
    if rpt and 'Bearer' in rpt:
        rpt = rpt.split(" ")[1]

    try:
        status = oxc.uma_rs_check_access(rpt=rpt, path=request.path, http_method=request.method)
    except OxdServerError as e:
        return jsonify({"error": "access denied", "description": str(e)})

    # If the rpt is not present, then act as the RP and get the RP
    if not rpt:
        rpt = oxc.uma_rp_get_rpt(status['ticket'])
        status = oxc.uma_rs_check_access(rpt=rpt['access_token'], path=request.path, http_method=request.method)

    if status['access'] == 'granted':
        return render_template('view_resource.html', resource=resource)
    else:
        return jsonify(status)


if __name__ == '__main__':
    app.run(debug=True, port=8085, ssl_context='adhoc')
