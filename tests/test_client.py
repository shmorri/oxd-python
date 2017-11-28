import os
import pytest

from mock import patch, Mock

from oxdpython.client import Client, Messenger, Configurer

from oxdpython.exceptions import OxdServerError

this_dir = os.path.dirname(os.path.realpath(__file__))
initial_config = os.path.join(this_dir, 'data', 'initial.cfg')
uma_config = os.path.join(this_dir, 'data', 'umaclient.cfg')


# --------------------------------------------------------------------------- #
# Register Site Command
# --------------------------------------------------------------------------- #
@patch.object(Configurer, 'set')
@patch.object(Messenger, 'send')
def test_register_site_command_updates_config_file(mock_send, mock_set):
    mock_send.return_value.status = 'ok'
    mock_send.return_value.data.oxd_id = 'test-id'

    c = Client(initial_config)
    c.oxd_id = None
    c.register_site()

    # Expected command dictionary to be sent to the messenger
    command = {
        'command': 'register_site',
        'params': {
            'authorization_redirect_uri': 'https://client.example.com/callback',
            'post_logout_redirect_uri': 'https://client.example.com/',
            'client_logout_uris': ['https://client.example.com/logout'],
            'client_name': 'oxdpython Test Client',
        }
    }
    mock_send.assert_called_with(command)
    mock_set.assert_called_with('oxd', 'id', 'test-id')


@patch.object(Messenger, 'send')
def test_register_raises_exception_for_invalid_auth_uri(mock_send):
    mock_send.return_value.status = 'error'
    mock_send.return_value.data.error = 'invalid_authorization_uri'
    mock_send.return_value.data.error_description = 'Invalid URI'

    config = os.path.join(this_dir, 'data', 'no_auth_uri.cfg')
    c = Client(config)

    with pytest.raises(OxdServerError):
        c.register_site()


# --------------------------------------------------------------------------- #
# Get Authorization URL Command
# --------------------------------------------------------------------------- #
@patch.object(Messenger, 'send')
def test_get_authorization_url(mock_send):
    mock_send.return_value.status = 'ok'
    mock_send.return_value.data.authorization_url = 'https://auth.url'
    c = Client(initial_config)
    auth_url = c.get_authorization_url()

    command = {
        'command': 'get_authorization_url',
        'params': {'oxd_id': 'test-id'}
    }
    mock_send.assert_called_with(command)
    assert auth_url == 'https://auth.url'


@patch.object(Configurer, 'set')
@patch.object(Messenger, 'send')
def test_get_authorization_url_works_without_explicit_site_registration(
        mock_send, mock_set):
    mock_send.return_value.status = 'ok'
    mock_send.return_value.data.oxd_id = 'new-registered-id'

    c = Client(initial_config)
    c.oxd_id = None
    c.get_authorization_url()

    command = {
        'command': 'get_authorization_url',
        # uses the new id to indicate it was registered implicitly
        'params': { 'oxd_id': 'new-registered-id'}
    }
    mock_send.assert_called_with(command)

@patch.object(Messenger, 'send')
def test_get_auth_url_accepts_optional_params(mock_send):
    mock_send.return_value.status = 'ok'
    mock_send.return_value.data.authorization_url = 'https://auth.url'
    c = Client(initial_config)
    command = {
        'command': 'get_authorization_url',
        'params': {
            'oxd_id': 'test-id'
        }
    }
    # acr values
    c.get_authorization_url(["basic", "gplus"])
    command['params']['acr_values'] = ['basic', 'gplus']
    mock_send.assert_called_with(command)

    # prompt
    c.get_authorization_url(["basic"], "login")
    command['params']['acr_values'] = ['basic']
    command['params']['prompt'] = 'login'
    mock_send.assert_called_with(command)

    # scope
    c.get_authorization_url(["basic"], scope=["openid", "profile", "email"])
    command['params'].pop('prompt')
    command['params']['scope'] = ["openid", "profile", "email"]
    mock_send.assert_called_with(command)


@patch.object(Messenger, 'send')
def test_get_authorization_url_sends_custom_parameters(mock_send):
    mock_send.return_value = Mock()
    mock_send.return_value.status = 'ok'
    mock_send.return_value.data.authorization_url = 'some url'
    c = Client(initial_config)

    c.get_authorization_url(custom_params=dict(key1='value1', key2='value2'))
    command = {
        'command': 'get_authorization_url',
        'params': {
            'oxd_id': c.oxd_id,
            'custom_parameters': dict(key1='value1', key2='value2')
        }
    }
    mock_send.assert_called_with(command)


# --------------------------------------------------------------------------- #
# Get Tokens by Code Command
# --------------------------------------------------------------------------- #
@patch.object(Messenger, 'send')
def test_get_tokens_by_code(mock_send):
    c = Client(initial_config)
    mock_send.return_value.status = "ok"
    mock_send.return_value.data = "mock-token"
    code = "code"
    state = "state"
    command = {"command": "get_tokens_by_code",
               "params": {
                   "oxd_id": c.oxd_id,
                   "code": code,
                   "state": state
                   }}
    token = c.get_tokens_by_code(code, state)
    mock_send.assert_called_with(command)
    assert token == "mock-token"


@patch.object(Messenger, 'send')
def test_get_tokens_raises_error_if_response_has_error(mock_send):
    c = Client(initial_config)
    mock_send.return_value.status = "error"
    mock_send.return_value.data.error = "MockError"
    mock_send.return_value.data.error_description = "No Tokens in Mock"

    with pytest.raises(OxdServerError):
        c.get_tokens_by_code("code", "state")


# --------------------------------------------------------------------------- #
# Get User Info Command
# --------------------------------------------------------------------------- #
@patch.object(Messenger, 'send')
def test_get_user_info(mock_send):
    c = Client(initial_config)
    mock_send.return_value.status = "ok"
    mock_send.return_value.data.claims = {"name": "mocky"}
    token = "token"
    command = {"command": "get_user_info",
               "params": {
                   "oxd_id": c.oxd_id,
                   "access_token": token
                   }}
    claims = c.get_user_info(token)
    mock_send.assert_called_with(command)
    assert claims == {"name": "mocky"}


@patch.object(Messenger, 'send')
def test_get_user_info_raises_error_on_oxd_error(mock_send):
    c = Client(initial_config)
    mock_send.return_value.status = "error"
    mock_send.return_value.data.error = "MockError"
    mock_send.return_value.data.error_description = "No Claims for mock"

    with pytest.raises(OxdServerError):
        c.get_user_info("some_token")


@patch.object(Messenger, 'send')
def test_get_logout_uri(mock_send):
    c = Client(initial_config)
    mock_send.return_value.status = "ok"
    mock_send.return_value.data.uri = "https://example.com/end_session"

    params = {"oxd_id": c.oxd_id}
    command = {"command": "get_logout_uri",
               "params": params}

    # called with no optional params
    c.get_logout_uri()
    mock_send.assert_called_with(command)

    # called with OPTIONAL id_token_hint
    uri = c.get_logout_uri("some_id")
    command["params"]["id_token_hint"] = "some_id"
    mock_send.assert_called_with(command)
    assert uri == "https://example.com/end_session"

    # called with OPTIONAL id_token_hint + post_logout_redirect_uri
    c.get_logout_uri("some_id", "https://some.site/logout")
    command["params"]["post_logout_redirect_uri"] = "https://some.site/logout"
    mock_send.assert_called_with(command)

    # called with OPTIONAL id_token_hint + post_logout_redirect_uri + state
    c.get_logout_uri("some_id", "https://some.site/logout", "some-s")
    command["params"]["state"] = "some-s"
    mock_send.assert_called_with(command)

    # called with OPTIONAL id_token_hint + post_logout_redirect_uri
    c.get_logout_uri("some_id", "https://some.site/logout", "some-s",
                           "some-ss")
    command["params"]["session_state"] = "some-ss"
    mock_send.assert_called_with(command)


@patch.object(Messenger, 'send')
def test_logout_raises_error_when_oxd_return_error(mock_send):
    c = Client(initial_config)
    mock_send.return_value.status = "error"
    mock_send.return_value.data.error = "MockError"
    mock_send.return_value.data.error_description = "Logout Mock Error"

    with pytest.raises(OxdServerError):
        c.get_logout_uri()


@patch.object(Messenger, 'send')
def test_update_site_registration(mock_send):
    mock_send.return_value.status = 'ok'
    c = Client(initial_config)
    c.config.set('client', 'post_logout_redirect_uri',
                 'https://client.example.com/')
    status = c.update_site_registration()
    assert status


@patch.object(Messenger, 'send')
def test_uma_rp_get_rpt(mock_send):
    c = Client(uma_config)
    c.oxd_id = 'dummy-id'

    # Just the ticket
    c.uma_rp_get_rpt('ticket-string')
    command = {'command': 'uma_rp_get_rpt',
               'params': {
                   'oxd_id': 'dummy-id',
                   'ticket': 'ticket-string'
               }}
    mock_send.assert_called_with(command)

    c.uma_rp_get_rpt('ticket-string', 'claim-token', 'claim-token-format',
                     'pct', 'rpt', ['openid', 'scope'], 'state')
    params = dict(ticket='ticket-string', claim_token='claim-token',
                  claim_token_format='claim-token-format', pct='pct',
                  rpt='rpt', scope=['openid', 'scope'], state='state',
                  oxd_id='dummy-id')
    command = dict(command='uma_rp_get_rpt', params=params)
    mock_send.assert_called_with(command)

@patch.object(Messenger, 'send')
def test_uma_rs_protect(mock_send):
    mock_send.return_value.status = 'ok'

    c = Client(uma_config)
    c.register_site()
    resources = [{"path": "/photo",
                  "conditions": [{
                      "httpMethods": ["GET"],
                      "scopes": ["http://photoz.example.com/dev/actions/view"]
                      }]
                  }]

    assert c.uma_rs_protect(resources)

