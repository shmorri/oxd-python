import os
import pytest
import unittest

from mock import patch, MagicMock

from oxdpython.client import Client, Configurer, Timer

from oxdpython.exceptions import OxdServerError, InvalidTicketError, \
    NeedInfoError

this_dir = os.path.dirname(os.path.realpath(__file__))
initial_config = os.path.join(this_dir, 'data', 'initial.cfg')
uma_config = os.path.join(this_dir, 'data', 'umaclient.cfg')
https_config = os.path.join(this_dir, 'data', 'https.cfg')

generic_error = {
    "status": "error",
    "data": {
        "error": "internal_error",
        "error_description": "something happened"
    }
}


class RegisterSiteTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status":"ok",
            "data": {
                "oxd_id":"6F9619FF-8B86-D011-B42D-00CF4FC964FF"
            }
        }

    @patch.object(Configurer, 'set')
    def test_config_file_updated_with_oxd_id(self, mock_set):
        c = Client(initial_config)
        c.msgr.request = MagicMock(return_value=self.success)
        c.oxd_id = None
        c.register_site()
        mock_set.assert_called_with('oxd', 'id',
                                    '6F9619FF-8B86-D011-B42D-00CF4FC964FF')

    def test_no_request_sent_if_already_registered(self):
        c = Client(initial_config)
        c.msgr.request = MagicMock(return_value=self.success)
        assert c.register_site() == 'test-id'
        c.msgr.request.assert_not_called()

    def test_raises_exception_when_oxd_returns_error(self):
        config = os.path.join(this_dir, 'data', 'no_auth_uri.cfg')
        c = Client(config)
        c.msgr.request = MagicMock(return_value=generic_error)
        with pytest.raises(OxdServerError):
            c.register_site()


class GetAuthUrlTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {
                "authorization_url": "https://server.example.com/authorize?"
            }
        }
        self.failure = generic_error
        self.c = Client(initial_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self):
        auth_url = self.c.get_authorization_url()
        assert auth_url == "https://server.example.com/authorize?"

    def test_call_with_optional_params(self):
        # Note: call_args is a tuple (args, kwargs) of the mock function call
        # By asserting that they are passed to the request function we assert
        # ensure that function under test is working as expected

        # acr values
        self.c.get_authorization_url(["basic", "gplus"])
        assert 'acr_values' in self.c.msgr.request.call_args[1]

        # prompt
        self.c.get_authorization_url(["basic"], "login")
        assert 'acr_values' in self.c.msgr.request.call_args[1]
        assert 'prompt' in self.c.msgr.request.call_args[1]

        # scope
        self.c.get_authorization_url(["basic"], scope=["openid", "profile"])
        assert 'acr_values' in self.c.msgr.request.call_args[1]
        assert 'scope' in self.c.msgr.request.call_args[1]

    def test_sending_custom_parameters(self):
        self.c.get_authorization_url(custom_params=dict(key1='value1', key2='value2'))
        assert 'custom_parameters' in self.c.msgr.request.call_args[1]

    def test_error_raised_on_oxd_server_error(self):
        self.c.msgr.request.return_value = self.failure
        with pytest.raises(OxdServerError):
            self.c.get_authorization_url()


class GetTokensByCodeTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok", "data": {
                "access_token": "SlAV32hkKG",
                "expires_in": 3600,
                "refresh_token": "aaAV32hkKG1",
                "id_token": "eyJ0afadZXso",
                "id_token_claims": {
                    "iss": "https://server.example.com",
                    "sub": "24400320",
                    "aud": "s6BhdRkqt3",
                    "nonce": "n-0S6_WzA2Mj",
                    "exp": 1311281970,
                    "iat": 1311280970,
                    "at_hash": "MTIzNDU2Nzg5MDEyMzQ1Ng"
                }
            }
        }
        self.failure = generic_error
        self.c = Client(initial_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self):
        token = self.c.get_tokens_by_code('code', 'state')
        assert token["access_token"] == "SlAV32hkKG"

    def test_error_raised_on_oxd_server_error(self):
        self.c.msgr.request.return_value = self.failure
        with pytest.raises(OxdServerError):
            self.c.get_tokens_by_code("code", "state")


class GetAccessTokenByRefreshTokenTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {
                "access_token": "SlAV32hkKG",
                "expires_in": 3600,
                "refresh_token": "aaAV32hkKG1"
            }
        }
        self.failure = generic_error
        self.c = Client(initial_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self):
        token = self.c.get_access_token_by_refresh_token('refresh_token')
        assert token['access_token'] == "SlAV32hkKG"

    def test_optional_parameters_are_passed(self):
        token = self.c.get_access_token_by_refresh_token('refresh_token',
                                                         ['openid', 'profile'])
        assert token['access_token'] == "SlAV32hkKG"
        assert 'scope' in self.c.msgr.request.call_args[1]

    def test_raises_error_on_oxd_server_error(self):
        self.c.msgr.request.return_value = self.failure
        with pytest.raises(OxdServerError):
            self.c.get_access_token_by_refresh_token('refresh_token')


class GetUserInfoTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {
                "claims": {
                    "sub": ["248289761001"],
                    "name": ["Jane Doe"],
                    "given_name": ["Jane"],
                    "family_name": ["Doe"],
                    "preferred_username": ["j.doe"],
                    "email": ["janedoe@example.com"],
                    "picture": ["http://example.com/janedoe/me.jpg"]
                }
            }
        }
        self.c = Client(initial_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self):
        claims = self.c.get_user_info('token')
        assert isinstance(claims, dict)
        assert "email" in claims

    def test_raises_error_on_oxd_error(self):
        self.c.msgr.request.return_value = generic_error
        with pytest.raises(OxdServerError):
            self.c.get_user_info("some_token")


class GetLogoutUriTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {
                "uri": "https://server.example.com/end_session?"
            }
        }
        self.c = Client(initial_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_get_logout_uri(self):
        # called with no optional params
        uri = self.c.get_logout_uri()
        assert "https://server.example.com/end_session?" == uri

        # called with OPTIONAL id_token_hint
        uri = self.c.get_logout_uri("some_id")
        assert "id_token_hint" in self.c.msgr.request.call_args[1]
        assert "https://server.example.com/end_session?" == uri

        # called with OPTIONAL id_token_hint + post_logout_redirect_uri
        self.c.get_logout_uri("some_id", "https://some.site/logout")
        assert "post_logout_redirect_uri" in self.c.msgr.request.call_args[1]

        # called with OPTIONAL id_token_hint + post_logout_redirect_uri + state
        self.c.get_logout_uri("some_id", "https://some.site/logout", "some-s")
        assert "state" in self.c.msgr.request.call_args[1]

        # called with OPTIONAL id_token_hint + post_logout_redirect_uri
        self.c.get_logout_uri("some_id", "https://some.site/logout", "state",
                              "session-state")
        assert "session_state" in self.c.msgr.request.call_args[1]

    def test_raises_error_when_oxd_return_error(self):
        self.c.msgr.request.return_value = generic_error
        with pytest.raises(OxdServerError):
            self.c.get_logout_uri()


class UpdateSiteTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {"status": "ok"}
        self.c = Client(initial_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self):
        self.c.config.set('client', 'post_logout_redirect_uri',
                          'https://client.example.com/')
        status = self.c.update_site()
        assert status

    def test_command_with_expires_time(self):
        status = self.c.update_site(client_secret_expires_at=12345)
        assert "client_secret_expires_at" in self.c.msgr.request.call_args[1]

    def test_raises_error_when_oxd_returns_error(self):
        self.c.msgr.request.return_value = generic_error
        with pytest.raises(OxdServerError):
            self.c.update_site()


class UmaRpGetRptTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {
                "access_token": "SSJHBSUSSJHVhjsgvhsgvshgsv",
                "token_type": "Bearer",
                "pct": "c2F2ZWRjb25zZW50",
                "upgraded": True
            }
        }
        self.needs_info = {
            "status": "error",
            "data": {
                "error": "need_info",
                "error_description": "The authorization server needs additional information in order to determine whether the client is authorized to have these permissions.",
                "details": {

                    "error": "need_info",
                    "ticket": "ZXJyb3JfZGV0YWlscw==",
                    "required_claims": [{
                        "claim_token_format": ["http://openid.net/specs/openid-connect-core-1_0.html#IDToken"],
                        "claim_type": "urn:oid:0.9.2342.19200300.100.1.3",
                        "friendly_name": "email",
                        "issuer": ["https://example.com/idp"],
                        "name": "email23423453ou453"
                    }],
                    "redirect_user": "https://as.example.com/rqp_claims?id=2346576421"
                }
            }
        }
        self.invalid_ticket = {
            "status": "error",
            "data": {
                "error": "invalid_ticket",
                "error_description":"Ticket is not valid (outdated or not present on Authorization Server)."
            }
        }
        self.failure = generic_error
        self.c = Client(uma_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self):
        # Just the ticket
        rpt = self.c.uma_rp_get_rpt('ticket-string')
        assert rpt['token_type'] == 'Bearer'

        # Call with all the parameters
        self.c.uma_rp_get_rpt('ticket-string', 'claim-token',
                              'claim-token-format', 'pct', 'rpt',
                              ['openid', 'scope'], 'state')
        assert 'claim_token_format' in self.c.msgr.request.call_args[1]
        assert 'rpt' in self.c.msgr.request.call_args[1]
        assert 'pct' in self.c.msgr.request.call_args[1]
        assert 'scope' in self.c.msgr.request.call_args[1]
        assert 'state' in self.c.msgr.request.call_args[1]

    def test_raises_error_for_oxd_internal_error(self):
        self.c.msgr.request.return_value = self.failure
        with pytest.raises(OxdServerError):
            self.c.uma_rp_get_rpt('ticket')

    def test_raises_invalid_ticket_error(self):
        self.c.msgr.request.return_value = self.invalid_ticket

        with pytest.raises(InvalidTicketError):
            self.c.uma_rp_get_rpt('ticket')

    def test_raises_need_info_error(self):
        self.c.msgr.request.return_value = self.needs_info

        with pytest.raises(NeedInfoError):
            self.c.uma_rp_get_rpt('ticket')


class UmaRsProtectTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {"status": "ok"}
        self.c = Client(uma_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self):
        resources = [{"path": "/photo",
                      "conditions": [{
                          "httpMethods": ["GET"],
                          "scopes": ["http://photoz.example.com/dev/actions/view"]
                          }]
                      }]

        assert self.c.uma_rs_protect(resources)

    def test_raises_error_on_oxd_server_error(self):
        self.c.msgr.request.return_value = generic_error

        with pytest.raises(OxdServerError):
            self.c.uma_rs_protect([])


class UmaRsCheckAccessTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {"access": "granted"}
        }
        self.denied_ticket = {
            "status": "ok",
            "data": {
                "access": "denied",
                "www-authenticate_header": "UMA realm=\"example\", as_uri =\"https://as.example.com\", error =\"insufficient_scope\", ticket =\"016f84e8-f9b9-11e0-bd6f-0021cc6004de\"",
                "ticket": "016f84e8-f9b9-11e0-bd6f-0021cc6004de"
            }
        }
        self.denied = {
            "status": "ok",
            "data": {
                "access": "denied"
            }
        }
        self.failure = {
            "status": "error",
            "data": {
                "error": "invalid_request",
                "error_description": "Resource is not protected. Please protect your resource first with uma_rs_protect command."
            }
        }
        self.c = Client(uma_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_returns_access_dict(self):
        response = self.c.uma_rs_check_access('rpt', '/photoz', 'GET')
        assert response["access"] == "granted"

        assert 'oxd_id' in self.c.msgr.request.call_args[1]
        assert 'rpt' in self.c.msgr.request.call_args[1]
        assert 'path' in self.c.msgr.request.call_args[1]
        assert 'http_method' in self.c.msgr.request.call_args[1]

    def test_raises_error_on_oxd_server_error(self):
        self.c.msgr.request.return_value = self.failure
        with pytest.raises(OxdServerError):
            self.c.uma_rs_check_access('rpt', '/photoz', 'GET')


class UmaRpGetClaimsGatherUrlTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {"url": "https://as.com/restv1/uma/gather_claims"}
        }
        self.c = Client(uma_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self):
        self.c.uma_rp_get_claims_gathering_url('ticket')
        assert 'oxd_id' in self.c.msgr.request.call_args[1]
        assert 'ticket' in self.c.msgr.request.call_args[1]
        assert 'claims_redirect_uri' in self.c.msgr.request.call_args[1]

    def test_raises_error_on_oxd_server_error(self):
        self.c.msgr.request.return_value = generic_error
        with pytest.raises(OxdServerError):
            self.c.uma_rp_get_claims_gathering_url('ticket')


class SetupClientTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {
                "oxd_id": "6F9619FF-8B86-D011-B42D-00CF4FC964FF",
                "op_host": "<op host>",
                "client_id": "<client id>",
                "client_secret": "<client secret>",
                "client_registration_access_token": "<Client registration access token>",
                "client_registration_client_uri": "<URI of client registration>",
                "client_id_issued_at": "<client_id issued at>",
                "client_secret_expires_at": "<client_secret expires at>"
            }
        }
        self.c = Client(initial_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    @patch.object(Configurer, 'set')
    def test_command(self, mock_set):
        assert self.c.setup_client()
        assert "authorization_redirect_uri" in self.c.msgr.request.call_args[1]
        assert "post_logout_redirect_uri" in self.c.msgr.request.call_args[1]
        assert "client_frontchannel_logout_uris" in self.c.msgr.request.call_args[1]

        mock_set.assert_any_call("client", "client_id", "<client id>")
        mock_set.assert_any_call("client", "client_secret", "<client secret>")
        mock_set.assert_any_call(
            "client", "client_registration_access_token",
            "<Client registration access token>"
        )

    def test_raises_error_when_oxd_server_errors(self):
        self.c.msgr.request.return_value = generic_error

        with pytest.raises(OxdServerError):
            self.c.setup_client()


@patch('oxdpython.client.Timer')
class GetClientTokenTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {
                "access_token": "6F9619FF-8B86-D011-B42D-00CF4FC964FF",
                "expires_in": 399,
                "refresh_token": "fr459f",
                "scope": "openid"
            }
        }
        self.c = Client(initial_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self, mock_timer):
        token = self.c.get_client_token()['access_token']
        assert token == "6F9619FF-8B86-D011-B42D-00CF4FC964FF"

        assert "client_id" in self.c.msgr.request.call_args[1]
        assert "client_secret" in self.c.msgr.request.call_args[1]
        assert "op_host" in self.c.msgr.request.call_args[1]

    def test_override_of_client_credentials(self, mock_timer):
        # Override value of client_id, client_secret and op_host
        self.c.get_client_token('client-id', 'client-secret', 'new-host')
        assert self.c.msgr.request.call_args[1]["client_id"] == 'client-id'
        assert self.c.msgr.request.call_args[1]["client_secret"] == 'client-secret'
        assert self.c.msgr.request.call_args[1]["op_host"] == 'new-host'

        # add optional arguments op_discovery_path and scope
        assert self.c.get_client_token('client-id', 'client-secret', 'new_host',
                                  'https://mag.el/lan', ['openid', 'profile'])
        assert self.c.msgr.request.call_args[1]['op_discovery_path'] == 'https://mag.el/lan'
        assert self.c.msgr.request.call_args[1]['scope'] == ['openid', 'profile']

    def test_throws_error_on_oxd_server_error(self, mock_timer):
        self.c.msgr.request.return_value = generic_error

        with pytest.raises(OxdServerError):
            self.c.get_client_token()


class RemoveSiteTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status": "ok",
            "data": {
                "oxd_id": "bcad760f-91ba-46e1-a020-05e4281d91b6"
            }
        }
        self.c = Client(initial_config)
        self.c.msgr.request = MagicMock(return_value=self.success)

    def test_command(self):
        assert self.c.remove_site()


