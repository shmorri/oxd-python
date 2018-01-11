import os
import oxdpython

from flask import Flask, render_template, request, jsonify, abort, make_response

app = Flask(__name__)
this_dir = os.path.dirname(os.path.realpath(__file__))
config = os.path.join(this_dir, 'rs-oxd.cfg')
oxc = oxdpython.Client(config)

resources = ['photos', 'docs']

photos = [{'id': 1, 'filename': 'https://example.com/photo1.jpg'}]
docs = [{'id': 1, 'filename': 'https://example.com/document1.pdf'}]

photos_counter = 1
docs_counter = 1

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/protect', methods=['POST'])
def protect():
    if not oxc.oxd_id:
        oxc.register_site()

    path = request.form.get('path')
    scope = request.form.get('scope').split(',')
    http_method = request.form.getlist('http_method')

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
        return render_template('index.html', status='protected', resource=path,
                               scope=scope, http_method=http_method)
    else:
        return render_template('index.html', status='failed', resource=path,
                               scope=scope, http_method=http_method)


@app.route('/api/<rtype>/', methods=['GET', 'POST'])
def api(rtype):
    """Function that fetches or adds a particular resource.

    :param rtype: resource type either photos or docs
    :return: json
    """
    status = {'access': 'granted'}
    try:
        rpt = request.headers.get('Authorization')
        if rpt:
            rpt = rpt.split()[1]
        status = oxc.uma_rs_check_access(rpt=rpt, path=request.path,
                                         http_method=request.method)
    except:
        print request.path, " seems unprotected"

    if not status['access'] == 'granted':
        return make_response(jsonify(status), 401)

    resource = docs
    counter = docs_counter
    if rtype in resources:
        if rtype == 'photos':
            resource = photos
            counter = photos_counter
    else:
        abort(404)

    if request.method == 'GET':
        return jsonify({rtype: resource})

    if request.method == 'POST':
        data = request.get_json()
        if 'filename' in data:
            counter += 1
            item = {'id': counter, 'filename': data['filename']}
            resource.append(item)
            return make_response(jsonify(item), 201)
        else:
            abort(400)

# --------------------------------------------------------------------------- #
# The /rp/get_rpt is a helper URL for the demo purposes. This should not be a
# part of the application unless the app is acting as both as a UMA Resource
# Server as well as the Requesting Party (RP).
# --------------------------------------------------------------------------- #
@app.route('/rp/get_rpt/')
def get_rpt():
    ticket = request.args.get('ticket')
    rpt = oxc.uma_rp_get_rpt(ticket)
    return jsonify(rpt)


if __name__ == '__main__':
    oxc.register_site()
    app.config.from_object('app_config')
    app.run(ssl_context='adhoc')

