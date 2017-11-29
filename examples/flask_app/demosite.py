import os
import uuid
import oxdpython

from flask import Flask, render_template, redirect, request, make_response

app = Flask(__name__)

this_dir = os.path.dirname(os.path.realpath(__file__))
config = os.path.join(this_dir, 'demosite.cfg')
oxc = oxdpython.Client(config)


@app.route('/')
def home():
    return render_template("home.html", url=request.path,
                           cookies=request.cookies)


@app.route('/authorize/')
def authorize():
    auth_url = oxc.get_authorization_url()
    return redirect(auth_url)


@app.route('/login_callback/')
def login_callback():
    # using request from Flask to parse the query string of the callback
    code = request.args.get('code')
    state = request.args.get('state')

    tokens = oxc.get_tokens_by_code(code, state)

    user = oxc.get_user_info(tokens.access_token)

    resp = make_response(render_template("login_callback.html", user=user,
                                         cookies=request.cookies))
    resp.set_cookie('sub', user.sub[0])
    resp.set_cookie('session_id', request.args.get('session_id'))
    return resp

@app.route('/browse_site/')
def browse_site():
    return render_template('home.html', url=request.path,
                           cookies=request.cookies)


@app.route('/logout/')
def logout():
    logout_url = oxc.get_logout_uri()
    return redirect(logout_url)


@app.route('/logout_callback/')
def logout_callback():
    """Route called by the OpenID provider when user logs out.

    Clear the cookies here.
    """
    resp = make_response('Logging Out')
    resp.set_cookie('user_sub', 'null', expires=0)
    resp.set_cookie('session_id', 'null', expires=0)
    print "cleared all the cookies"
    return resp


@app.route('/post_logout/')
def post_logout():
    return render_template("home.html", url=request.path,
                           cookies=request.cookies)


if __name__ == "__main__":
    app.run(debug=True, port=8080, ssl_context='adhoc')
