import os
import pytest
import unittest

from mock import patch, Mock

from oxdpython.client import Client, Messenger, Configurer

from oxdpython.exceptions import OxdServerError

this_dir = os.path.dirname(os.path.realpath(__file__))
initial_config = os.path.join(this_dir, 'data', 'initial.cfg')
uma_config = os.path.join(this_dir, 'data', 'umaclient.cfg')


class RegisterSiteTestCase(unittest.TestCase):
    @patch.object(Configurer, 'set')
    @patch.object(Messenger, 'send')
    def test_command_updates_config_file(self, mock_send, mock_set):
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
                'client_frontchannel_logout_uris': ['https://client.example.com/logout'],
                'client_name': 'oxdpython Test Client',
            }
        }
        mock_send.assert_called_with(command)
        mock_set.assert_called_with('oxd', 'id', 'test-id')

    @patch.object(Messenger, 'send')
    def test_raises_exception_for_invalid_auth_uri(self, mock_send):
        mock_send.return_value.status = 'error'

        config = os.path.join(this_dir, 'data', 'no_auth_uri.cfg')
        c = Client(config)

        with pytest.raises(OxdServerError):
            c.register_site()


class GetAuthUrlTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_command(self, mock_send):
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
    def test_automatic_site_registration(self, mock_send, mock_set):
        mock_send.return_value.status = 'ok'
        mock_send.return_value.data.oxd_id = 'new-registered-id'

        c = Client(initial_config)
        c.oxd_id = None
        c.get_authorization_url()

        command = {
            'command': 'get_authorization_url',
            # uses the new id to indicate it was registered implicitly
            'params': {'oxd_id': 'new-registered-id'}
        }
        mock_send.assert_called_with(command)

    @patch.object(Messenger, 'send')
    def test_call_with_optional_params(self, mock_send):
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
    def test_sending_custom_parameters(self, mock_send):
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

    @patch.object(Messenger, 'send')
    def test_error_raised_on_oxd_server_error(self, mock_send):
        c = Client(initial_config)
        mock_send.return_value.status = "error"

        with pytest.raises(OxdServerError):
            c.get_authorization_url()


class GetTokensByCodeTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_command(self, mock_send):
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
    def test_error_raised_on_oxd_server_error(self, mock_send):
        c = Client(initial_config)
        mock_send.return_value.status = "error"

        with pytest.raises(OxdServerError):
            c.get_tokens_by_code("code", "state")


class GetAccessTokenByRefreshTokenTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_command(self, mock_send):
        c = Client(initial_config)
        assert c.get_access_token_by_refresh_token('refresh_token')

        command = {
            "command": "get_access_token_by_refresh_token",
            "params": {
                "oxd_id": "test-id",
                "refresh_token": "refresh_token"
            }
        }
        mock_send.assert_called_with(command)

    @patch.object(Messenger, 'send')
    def test_optional_parameters_are_passed(self, mock_send):
        c = Client(initial_config)
        assert c.get_access_token_by_refresh_token('refresh_token',
                                                   ['openid', 'profile'])

        command = {
            "command": "get_access_token_by_refresh_token",
            "params": {
                "oxd_id": "test-id",
                "refresh_token": "refresh_token",
                "scope": ["openid", "profile"]
            }
        }
        mock_send.assert_called_with(command)

    @patch.object(Messenger, 'send')
    def test_raises_error_on_oxd_server_error(self, mock_send):
        mock_send.return_value.status = 'error'
        c = Client(initial_config)
        with pytest.raises(OxdServerError):
            c.get_access_token_by_refresh_token('refresh_token')


class GetUserInfoTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_command(self, mock_send):
        mock_send.return_value.status = "ok"
        token = "token"
        command = {"command": "get_user_info",
                   "params": {
                       "oxd_id": 'test-id',
                       "access_token": token
                       }}

        c = Client(initial_config)
        c.get_user_info(token)
        mock_send.assert_called_with(command)

    @patch.object(Messenger, 'send')
    def test_raises_error_on_oxd_error(self, mock_send):
        c = Client(initial_config)
        mock_send.return_value.status = "error"

        with pytest.raises(OxdServerError):
            c.get_user_info("some_token")


class GetLogoutUriTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_get_logout_uri(self, mock_send):
        mock_send.return_value.status = "ok"
        mock_send.return_value.data.uri = "https://example.com/end_session"

        params = {"oxd_id": "test-id"}
        command = {"command": "get_logout_uri",
                   "params": params}

        # called with no optional params
        c = Client(initial_config)
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
    def test_raises_error_when_oxd_return_error(self, mock_send):
        c = Client(initial_config)
        mock_send.return_value.status = "error"

        with pytest.raises(OxdServerError):
            c.get_logout_uri()


class UpdateSiteRegistrationTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_command(self, mock_send):
        mock_send.return_value.status = 'ok'
        c = Client(initial_config)
        c.config.set('client', 'post_logout_redirect_uri',
                     'https://client.example.com/')
        status = c.update_site_registration()
        assert status

    @patch.object(Messenger, 'send')
    def test_raises_error_when_oxd_returns_error(self, mock_send):
        mock_send.return_value.status = 'error'

        c = Client(initial_config)
        with pytest.raises(OxdServerError):
            c.update_site_registration()


class UmaRpGetRptTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_command(self, mock_send):
        c = Client(uma_config)

        # Just the ticket
        c.uma_rp_get_rpt('ticket-string')
        command = {'command': 'uma_rp_get_rpt',
                   'params': {
                       'oxd_id': 'test-id',
                       'ticket': 'ticket-string'
                   }}
        mock_send.assert_called_with(command)

        # Call with all the parameters
        c.uma_rp_get_rpt('ticket-string', 'claim-token', 'claim-token-format',
                         'pct', 'rpt', ['openid', 'scope'], 'state')
        params = dict(ticket='ticket-string', claim_token='claim-token',
                      claim_token_format='claim-token-format', pct='pct',
                      rpt='rpt', scope=['openid', 'scope'], state='state',
                      oxd_id='test-id')
        command = dict(command='uma_rp_get_rpt', params=params)
        mock_send.assert_called_with(command)

    @patch.object(Messenger, 'send')
    def test_raises_error_for_oxd_internal_error(self, mock_send):
        mock_send.return_value.status = 'error'
        mock_send.return_value.data.error = 'internal_error'

        c = Client(uma_config)
        with pytest.raises(OxdServerError):
            c.uma_rp_get_rpt('ticket')

    @patch.object(Messenger, 'send')
    def test_return_data_for_other_errors(self, mock_send):
        mock_send.return_value.status = 'error'
        mock_send.return_value.data.error = 'need_info'

        c = Client(uma_config)
        assert c.uma_rp_get_rpt('ticket')


class UmaRsProtectTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_command(self, mock_send):
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

    @patch.object(Messenger, 'send')
    def test_raises_error_on_oxd_server_error(self, mock_send):
        mock_send.return_value.status = 'error'

        c = Client(uma_config)
        with pytest.raises(OxdServerError):
            c.uma_rs_protect([])


class UmaRsCheckAccessTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_uma_rs_check_access(self, mock_send):
        mock_send.return_value.status = 'ok'
        mock_send.return_value.data = {'access': 'granted'}

        c = Client(uma_config)
        assert c.uma_rs_check_access('rpt', '/photoz', 'GET')

        command = {
            'command': 'uma_rs_check_access',
            'params': {
                'oxd_id': 'test-id',
                'rpt': 'rpt',
                'path': '/photoz',
                'http_method': 'GET'
            }
        }
        mock_send.assert_called_with(command)

    @patch.object(Messenger, 'send')
    def test_raises_error_on_oxd_server_error(self, mock_send):
        mock_send.return_value.status = 'error'

        c = Client(uma_config)
        with pytest.raises(OxdServerError):
            c.uma_rs_check_access('rpt', '/photoz', 'GET')

class UmaRpGetClaimsGatherUrlTestCase(unittest.TestCase):
    @patch.object(Messenger, 'send')
    def test_command(self, mock_send):
        c = Client(uma_config)
        assert c.uma_rp_get_claims_gathering_url('ticket')

        command = {
            'command': 'uma_rp_get_claims_gathering_url',
            'params': {
                'oxd_id': 'test-id',
                'ticket': 'ticket',
                'claims_redirect_uri': 'https://dummy-uma.client.org/claims_cb'
            }
        }
        mock_send.assert_called_with(command)

    @patch.object(Messenger, 'send')
    def test_raises_error_on_oxd_server_error(self, mock_send):
        mock_send.return_value.status = 'error'

        c = Client(uma_config)
        with pytest.raises(OxdServerError):
            c.uma_rp_get_claims_gathering_url('ticket')


class SetupClientTestCase(unittest.TestCase):
    @patch.object(Configurer, 'set')
    @patch.object(Messenger, 'send')
    def test_command(self, mock_send, mock_set):
        mock_send.return_value.status = 'ok'

        c = Client(initial_config)
        c.oxd_id = None
        assert c.setup_client()

        command = {
            "command": "setup_client",
            "params": {
                "authorization_redirect_uri":
                    "https://client.example.com/callback",
                "post_logout_redirect_uri": "https://client.example.com/",
                "client_frontchannel_logout_uris":
                    ["https://client.example.com/logout"],
                "client_name": "oxdpython Test Client"
            }
        }
        mock_send.assert_called_with(command)

    @patch.object(Messenger, 'send')
    def test_raises_error_when_oxd_server_errors(self, mock_send):
        mock_send.return_value.status = 'error'

        c = Client(initial_config)
        c.oxd_id = None
        with pytest.raises(OxdServerError):
            c.setup_client()

    @patch.object(Configurer, 'set')
    @patch.object(Messenger, 'send')
    def test_set_client_credentials_upon_setup(self, mock_send, mock_set):
        mock_send.return_value.status = 'ok'
        mock_send.return_value.data.oxd_id = "returned-id"
        mock_send.return_value.data.client_id = "client-id"
        mock_send.return_value.data.client_secret = "client-secret"

        c = Client(initial_config)
        c.oxd_id = None
        assert c.setup_client()

        mock_set.assert_any_call("oxd", "id", "returned-id")
        mock_set.assert_any_call("client", "client_id", "client-id")
        mock_set.assert_any_call("client", "client_secret", "client-secret")
