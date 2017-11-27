import os
import pytest

from mock import patch

from oxdpython import Client
from oxdpython.messenger import Messenger

this_dir = os.path.dirname(os.path.realpath(__file__))
config_location = os.path.join(this_dir, 'data', 'initial.cfg')
uma_config = os.path.join(this_dir, 'data', 'umaclient.cfg')


def test_initializes_with_config():
    c = Client(config_location)
    assert c.config.get('oxd', 'port') == '8099'
    assert isinstance(c.msgr, Messenger)
    assert c.authorization_redirect_uri == "https://client.example.com/callback"


def test_register_site_command():
    # preset register client command response
    c = Client(config_location)
    c.oxd_id = None
    assert c.oxd_id is None
    c.register_site()
    assert c.oxd_id is not None


def test_register_raises_runtime_error_for_oxd_error_response():
    # no_oxdid.cfg doesn't have the required param `authorization_redirect_uri`
    # empty. So the client registration should fail
    config = os.path.join(this_dir, 'data', 'no_oxdid.cfg')
    c = Client(config)
    with pytest.raises(RuntimeError):
        c.register_site()


def test_get_authorization_url():
    c = Client(config_location)
    auth_url = c.get_authorization_url()
    assert 'callback' in auth_url


def test_get_authorization_url_works_without_explicit_site_registration():
    c = Client(config_location)
    c.oxd_id = None  # assume the client isn't registered
    auth_url = c.get_authorization_url()
    assert 'callback' in auth_url


def test_get_auth_url_accepts_optional_params():
    c = Client(config_location)
    # acr values
    auth_url = c.get_authorization_url(["basic", "gplus"])
    assert 'basic' in auth_url
    assert 'gplus' in auth_url

    # prompt
    auth_url = c.get_authorization_url(["basic"], "login")
    assert 'basic' in auth_url
    assert 'prompt' in auth_url

    # scope
    auth_url = c.get_authorization_url(["basic"], None,
                                       ["openid", "profile", "email"])
    assert 'openid' in auth_url
    assert 'profile' in auth_url
    assert 'email' in auth_url


@patch.object(Messenger, 'send')
def test_get_tokens_by_code(mock_send):
    c = Client(config_location)
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
    c = Client(config_location)
    mock_send.return_value.status = "error"
    mock_send.return_value.data.error = "MockError"
    mock_send.return_value.data.error_description = "No Tokens in Mock"

    with pytest.raises(RuntimeError):
        c.get_tokens_by_code("code", "state")


@patch.object(Messenger, 'send')
def test_get_user_info(mock_send):
    c = Client(config_location)
    mock_send.return_value.status = "ok"
    mock_send.return_value.data.claims = {"name": "mocky"}
    token = "tokken"
    command = {"command": "get_user_info",
               "params": {
                   "oxd_id": c.oxd_id,
                   "access_token": token
                   }}
    claims = c.get_user_info(token)
    mock_send.assert_called_with(command)
    assert claims == {"name": "mocky"}


def test_get_user_info_raises_erro_on_invalid_args():
    c = Client(config_location)
    # Empty code should raise error
    with pytest.raises(RuntimeError):
        c.get_user_info("")


@patch.object(Messenger, 'send')
def test_get_user_info_raises_error_on_oxd_error(mock_send):
    c = Client(config_location)
    mock_send.return_value.status = "error"
    mock_send.return_value.data.error = "MockError"
    mock_send.return_value.data.error_description = "No Claims for mock"

    with pytest.raises(RuntimeError):
        c.get_user_info("some_token")


@patch.object(Messenger, 'send')
def test_logout(mock_send):
    c = Client(config_location)
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

    # called wiht OPTIONAL id_token_hint + post_logout_redirect_uri
    c.get_logout_uri("some_id", "https://some.site/logout")
    command["params"]["post_logout_redirect_uri"] = "https://some.site/logout"
    mock_send.assert_called_with(command)

    # called wiht OPTIONAL id_token_hint + post_logout_redirect_uri + state
    c.get_logout_uri("some_id", "https://some.site/logout", "some-s")
    command["params"]["state"] = "some-s"
    mock_send.assert_called_with(command)

    # called wiht OPTIONAL id_token_hint + post_logout_redirect_uri
    c.get_logout_uri("some_id", "https://some.site/logout", "some-s",
                           "some-ss")
    command["params"]["session_state"] = "some-ss"
    mock_send.assert_called_with(command)


@patch.object(Messenger, 'send')
def test_logout_raises_error_when_oxd_return_error(mock_send):
    c = Client(config_location)
    mock_send.return_value.status = "error"
    mock_send.return_value.data.error = "MockError"
    mock_send.return_value.data.error_description = "Logout Mock Error"

    with pytest.raises(RuntimeError):
        c.get_logout_uri()


def test_update_site_registration():
    c = Client(config_location)
    c.config.set('client', 'post_logout_redirect_uri',
                 'https://client.example.com/')
    status = c.update_site_registration()
    assert status

@patch.object(Messenger, 'send')
def test_uma_rp_get_rpt(mock_send):
    c = Client(uma_config)

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


def test_uma_rp_authorize_rpt():
    c = Client(uma_config)
    rpt = 'dummy_rpt'
    ticket = 'dummy_ticket'
    status = c.uma_rp_authorize_rpt(rpt, ticket)
    assert status


def test_uma_rp_authorize_rpt_throws_errors():
    c = Client(uma_config)
    rpt = 'invalid_rpt'
    ticket = 'invalid_ticket'
    response = c.uma_rp_authorize_rpt(rpt, ticket)
    assert response.status == 'error'


def test_uma_rp_get_gat():
    c = Client(uma_config)
    scopes = ["http://photoz.example.com/dev/actions/view",
              "http://photoz.example.com/dev/actions/add"]
    gat = c.uma_rp_get_gat(scopes)
    assert isinstance(gat, str)


def test_uma_rs_protect():
    c = Client(uma_config)
    resources = [{"path": "/photo",
                  "conditions": [{
                      "httpMethods": ["GET"],
                      "scopes": ["http://photoz.example.com/dev/actions/view"]
                      }]
                  }]

    assert c.uma_rs_protect(resources)
