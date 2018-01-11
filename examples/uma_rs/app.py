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

app.config['FIRST_RUN'] = True
app.config['photos'] = 1
app.config['docs'] = 1

@app.route('/')
def index():
    if app.config.get('FIRST_RUN'):
        return render_template('setup.html')
    return render_template('index.html')

@app.route('/setup/')
def setup_resource_server():
    oxc.register_site()
    resources = [
        {
            "path": "/api/photos/",
            "conditions": [
                {
                    "httpMethods": ["GET"],
                    "scopes": ["https://resource.example.com/uma/scope/view"]
                },
                {
                    "httpMethods": ["POST"],
                    "scopes": ["https://resource.example.com/uma/scope/add"]
                },
                {
                    "httpMethods": ["GET", "POST"],
                    "scopes": ["https://resource.example.com/uma/scope/all"]
                }
            ]
        }
    ]
    protected = oxc.uma_rs_protect(resources)
    if protected:
        app.config['FIRST_RUN'] = False
        return render_template("index.html")


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

    if rtype not in resources:
        abort(404)

    if rtype == 'photos':
        resource = photos
        counter = app.config.get('photos')
    else:
        resource = docs
        counter = app.config.get('docs')

    if request.method == 'GET':
        return jsonify({rtype: resource})

    if request.method == 'POST':
        data = request.get_json()
        if 'filename' in data:
            counter += 1
            item = {'id': counter, 'filename': data['filename']}
            resource.append(item)
            if rtype == 'photos':
                app.config['photos'] = counter
            else:
                app.config['docs'] = counter
            return make_response(jsonify(item), 201)
        else:
            abort(400)


if __name__ == '__main__':
    app.config.from_object('app_config')
    app.run(ssl_context='adhoc')

