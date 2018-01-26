import os
import argparse
import traceback
import logging
import urlparse

from oxdpython import Client


def test_openid_commands(config_file):
    """function that runs the commands in a interactive manner

    :param config_file: config file location
    """
    c = Client(config_file)

    print "\n=> Setup Client"
    setup_data = c.setup_client()
    logging.info("Received: %s", setup_data)

    print "\n=> Get Client Token"
    tokens = c.get_client_token(auto_update=False)
    logging.info("Received: %s", tokens)

    print "\n=> Update site registration"
    updated = c.update_site()
    c.config.set("client", "scope", "openid,profile")
    logging.info("Received: %s", updated)

    print "\n=> Getting auth URL"
    auth_url = c.get_authorization_url()
    print "Visit this URL in your browser: ", auth_url
    logging.info("Received: %s", auth_url)

    print "\n=> Getting tokens by code"
    callback_url = raw_input("Enter redirected URL to parse tokens: ")
    parsed = urlparse.urlparse(callback_url)
    params = urlparse.parse_qs(parsed.query)
    tokens = c.get_tokens_by_code(params['code'][0], params['state'][0])
    logging.info("Received: %s", tokens)

    print "\n=> Getting user info"
    claims = c.get_user_info(tokens['access_token'])
    logging.info("Received: %s", claims)

    print "\n=> Getting new access token using refresh token"
    new_token = c.get_access_token_by_refresh_token(tokens["refresh_token"])
    logging.info("Received: %s", new_token)

    print "\n=> Getting Logout URI"
    logout_uri = c.get_logout_uri()
    logging.info("Received: %s", logout_uri)
    print "Visit this URL to logout: ", logout_uri

    print "\n=> Remove Site"
    oxd_id = c.remove_site()
    logging.info("Received: %s", oxd_id)

def execute_test(test):
    config = os.path.join(this_dir, 'openid_https.cfg')
    test_config = os.path.join(this_dir, 'test.cfg')

    with open(test_config, 'w') as of:
        with open(config) as f:
            of.write(f.read())

    try:
        test(test_config)
    except:
        print traceback.format_exc()

    os.remove(test_config)

if __name__ == '__main__':
    this_dir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    tests = [test_openid_commands]

    for test in tests:
        execute_test(test)

    print "All tests complete."


