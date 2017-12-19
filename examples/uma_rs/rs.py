import os
import oxdpython

from flask import Flask, render_template, redirect, request, make_response, url_for, jsonify

app = Flask(__name__)

this_dir = os.path.dirname(os.path.realpath(__file__))
config = os.path.join(this_dir, 'rs.cfg')
oxc = oxdpython.Client(config)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/protect', methods=['GET', 'POST'])
def protect():
    if not oxc.oxd_id:
        oxc.register_site()

    if request.method == 'POST':
        path = request.form.get('path')
        scope = request.form.get('scope')
        http_method = request.form.get('http_method')

        resources = [
            {
                "path" : path,
                "conditions": [{
                    "httpMethods": [http_method],
                    "scopes": [scope]
                }]
            }
        ]

        print oxc.uma_rs_protect(resources)

    return redirect(url_for('home'))

@app.route('/photos')
def photos():
    status = oxc.uma_rs_check_access(rpt='', path='/photos', http_method='GET')
    return jsonify(status)


if __name__ == '__main__':
    app.run(debug=True, port=8085, ssl_context='adhoc')
