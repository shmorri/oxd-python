import os
import logging
import urlparse

from oxdpython import Client

logging.basicConfig(level=logging.DEBUG)


def run_commands(config):
    """function that runs the commands in a interactive manner

    :param config: config file location
    """
    c = Client(config)

    logging.info("Calling setup_client()")
    setup_data = c.setup_client()
    logging.info("Received: %s", setup_data)

    logging.info("Calling get_client_token()")
    tokens = c.get_client_token()
    assert 'access_token' in tokens
    logging.info("Received: %s", tokens)

    logging.info("Registering client using register_site()")
    oxd_id = c.register_site()
    logging.info("Received: %s", oxd_id)

    logging.info("Getting auth URL")
    auth_url = c.get_authorization_url()
    print "Visit this URL in your browser: ", auth_url
    logging.info("Received: %s", auth_url)

    callback_url = raw_input("Enter redirect URL: ")
    parsed = urlparse.urlparse(callback_url)
    params = urlparse.parse_qs(parsed.query)

    logging.info("Getting tokens by code")
    tokens = c.get_tokens_by_code(params['code'][0], params['state'][0])
    logging.info("Received: %s", tokens)

    logging.info("Getting user info")
    claims = c.get_user_info(tokens['access_token'])
    logging.info("Received: %s", claims)

    logging.info("Getting new access token using refresh token")
    new_token = c.get_access_token_by_refresh_token(tokens["refresh_token"])
    logging.info("Received: %s", new_token)

    logging.info("Update site registration")
    updated = c.update_site_registration()
    c.config.set("client", "scope", "openid,profile")
    logging.info("Received: %s", updated)

    logging.info("Getting Logout URI")
    logout_uri = c.get_logout_uri()
    logging.info("Received: %s", logout_uri)
    print "Visit this URL to logout: ", logout_uri

if __name__ == '__main__':
    this_dir = os.path.dirname(os.path.realpath(__file__))
    config = os.path.join(this_dir, 'openid_socket.cfg')
    test_config = os.path.join(this_dir, 'test.cfg')

    with open(test_config, 'w') as of:
        with open(config) as f:
            of.write(f.read())

    run_commands(test_config)
    os.remove(test_config)

