import os
import pytest
import unittest

from mock import patch, Mock, MagicMock

from oxdpython.client import Client, Messenger, Configurer

from oxdpython.exceptions import OxdServerError, InvalidTicketError, \
    NeedInfoError

this_dir = os.path.dirname(os.path.realpath(__file__))
initial_config = os.path.join(this_dir, 'data', 'initial.cfg')
uma_config = os.path.join(this_dir, 'data', 'umaclient.cfg')
https_config = os.path.join(this_dir, 'data', 'https.cfg')

generic_error = {
    "status": "error",
    "data": { "error": "internal_error",
              "error_description": "something happened"
    }
}


@patch.object(Messenger, 'request')
class RegisterSiteTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status":"ok",
            "data": {
                "oxd_id":"6F9619FF-8B86-D011-B42D-00CF4FC964FF"
            }
        }
        self.failure = generic_error

    @patch.object(Configurer, 'set')
    def test_config_file_updated_with_oxd_id(self, mock_set, request):
        request.return_value = self.success

        c = Client(initial_config)
        c.oxd_id = None
        c.register_site()
        mock_set.assert_called_with('oxd', 'id',
                                    '6F9619FF-8B86-D011-B42D-00CF4FC964FF')

    def test_no_request_sent_if_already_registered(self, request):
        c = Client(initial_config)
        assert c.register_site() == 'test-id'
        request.assert_not_called()

    def test_raises_exception_when_oxd_returns_error(self, request):
        request.return_value = self.failure

        config = os.path.join(this_dir, 'data', 'no_auth_uri.cfg')
        c = Client(config)
        with pytest.raises(OxdServerError):
            c.register_site()


@patch.object(Messenger, 'request')
class GetAuthUrlTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status":"ok",
            "data": {
                "authorization_url": "https://server.example.com/authorize?"
            }
        }
        self.failure = generic_error
        self.c = Client(initial_config)

    def test_command(self, request):
        request.return_value = self.success

        auth_url = self.c.get_authorization_url()
        assert auth_url == "https://server.example.com/authorize?"

    def test_automatic_site_registration(self, request):
        request.return_value = self.success

        c = Client(initial_config)
        c.oxd_id = None
        c.register_site = MagicMock()

        auth_url = c.get_authorization_url()
        c.register_site.assert_called_with()
        assert auth_url == "https://server.example.com/authorize?"

    def test_call_with_optional_params(self, request):
        request.return_value = self.success

        # Note: call_args is a tuple (args, kwargs) of the mock function call
        # By asserting that they are passed to the request function we assert
        # ensure that function under test is working as expected

        # acr values
        self.c.get_authorization_url(["basic", "gplus"])
        assert 'acr_values' in request.call_args[1]

        # prompt
        self.c.get_authorization_url(["basic"], "login")
        assert 'acr_values' in request.call_args[1]
        assert 'prompt' in request.call_args[1]

        # scope
        self.c.get_authorization_url(["basic"], scope=["openid", "profile"])
        assert 'acr_values' in request.call_args[1]
        assert 'scope' in request.call_args[1]

    def test_sending_custom_parameters(self, request):
        request.return_value = self.success

        self.c.get_authorization_url(custom_params=dict(key1='value1', key2='value2'))
        assert 'custom_parameters' in request.call_args[1]

    def test_error_raised_on_oxd_server_error(self, request):
        request.return_value = self.failure

        with pytest.raises(OxdServerError):
            self.c.get_authorization_url()


@patch.object(Messenger, 'request')
class GetTokensByCodeTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status":"ok", "data": {
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

    def test_command(self, request):
        request.return_value = self.success

        token = self.c.get_tokens_by_code('code', 'state')
        assert token["access_token"]  == "SlAV32hkKG"

    def test_error_raised_on_oxd_server_error(self, request):
        request.return_value = self.failure
        with pytest.raises(OxdServerError):
            self.c.get_tokens_by_code("code", "state")


@patch.object(Messenger, 'request')
class GetAccessTokenByRefreshTokenTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status":"ok",
            "data": {
                "access_token":"SlAV32hkKG",
                "expires_in":3600,
                "refresh_token":"aaAV32hkKG1"
            }
        }
        self.failure = generic_error
        self.c = Client(initial_config)

    def test_command(self, request):
        request.return_value = self.success

        token =  self.c.get_access_token_by_refresh_token('refresh_token')
        assert token['access_token'] == "SlAV32hkKG"

    def test_optional_parameters_are_passed(self, request):
        request.return_value = self.success

        token = self.c.get_access_token_by_refresh_token('refresh_token',
                                                         ['openid', 'profile'])
        assert token['access_token'] == "SlAV32hkKG"
        assert 'scope' in request.call_args[1]

    def test_raises_error_on_oxd_server_error(self, request):
        request.return_value = generic_error
        with pytest.raises(OxdServerError):
            self.c.get_access_token_by_refresh_token('refresh_token')


@patch.object(Messenger, 'request')
class GetUserInfoTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status":"ok",
            "data":{
                "claims":{
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

    def test_command(self, request):
        request.return_value = self.success

        claims = self.c.get_user_info('token')
        assert "email" in claims

    def test_raises_error_on_oxd_error(self, request):
        request.return_value = generic_error

        with pytest.raises(OxdServerError):
            self.c.get_user_info("some_token")


@patch.object(Messenger, 'request')
class GetLogoutUriTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status":"ok",
            "data": {
                "uri": "https://server.example.com/end_session?"
            }
        }
        self.c = Client(initial_config)

    def test_get_logout_uri(self, request):
        request.return_value = self.success

        # called with no optional params
        uri = self.c.get_logout_uri()
        assert  "https://server.example.com/end_session?" == uri

        # called with OPTIONAL id_token_hint
        uri = self.c.get_logout_uri("some_id")
        assert "id_token_hint" in request.call_args[1]
        assert  "https://server.example.com/end_session?" == uri

        # called with OPTIONAL id_token_hint + post_logout_redirect_uri
        self.c.get_logout_uri("some_id", "https://some.site/logout")
        assert "post_logout_redirect_uri" in request.call_args[1]

        # called with OPTIONAL id_token_hint + post_logout_redirect_uri + state
        self.c.get_logout_uri("some_id", "https://some.site/logout", "some-s")
        assert "state" in request.call_args[1]

        # called with OPTIONAL id_token_hint + post_logout_redirect_uri
        self.c.get_logout_uri("some_id", "https://some.site/logout", "state",
                         "session-state")
        assert "session_state" in request.call_args[1]

    def test_raises_error_when_oxd_return_error(self, request):
        request.return_value = generic_error
        with pytest.raises(OxdServerError):
            self.c.get_logout_uri()


@patch.object(Messenger, 'request')
class UpdateSiteRegistrationTestCase(unittest.TestCase):
    def test_command(self, request):
        request.return_value = {"status":"ok"}

        c = Client(initial_config)
        c.config.set('client', 'post_logout_redirect_uri',
                     'https://client.example.com/')
        status = c.update_site_registration()
        assert status

    def test_raises_error_when_oxd_returns_error(self, request):
        request.return_value = generic_error

        c = Client(initial_config)
        with pytest.raises(OxdServerError):
            c.update_site_registration()


@patch.object(Messenger, 'request')
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
                "error":"need_info",
                "error_description": "The authorization server needs additional information in order to determine whether the client is authorized to have these permissions.",
                "details": {
                    "error":"need_info",
                    "ticket":"ZXJyb3JfZGV0YWlscw==",
                    "required_claims": [{
                        "claim_token_format":[
                            "http://openid.net/specs/openid-connect-core-1_0.html#IDToken"
                        ],
                    "claim_type":"urn:oid:0.9.2342.19200300.100.1.3",
                    "friendly_name":"email",
                    "issuer":["https://example.com/idp"],
                    "name":"email23423453ou453"
                    }],
                    "redirect_user":"https://as.example.com/rqp_claims?id=2346576421"
                }
            }
        }
        self.invalid_ticket = {
            "status":"error",
            "data": {
                "error":"invalid_ticket",
                "error_description":"Ticket is not valid (outdated or not present on Authorization Server)."
            }
        }
        self.c = Client(uma_config)

    def test_command(self, request):
        request.return_value = self.success

        # Just the ticket
        rpt = self.c.uma_rp_get_rpt('ticket-string')
        assert rpt['token_type'] == 'Bearer'

        # Call with all the parameters
        self.c.uma_rp_get_rpt('ticket-string', 'claim-token',
                              'claim-token-format', 'pct', 'rpt',
                              ['openid', 'scope'], 'state')
        assert 'claim_token_format' in request.call_args[1]
        assert 'rpt' in request.call_args[1]
        assert 'pct' in request.call_args[1]
        assert 'scope' in request.call_args[1]
        assert 'state' in request.call_args[1]

    def test_raises_error_for_oxd_internal_error(self, request):
        request.return_value = generic_error

        with pytest.raises(OxdServerError):
            self.c.uma_rp_get_rpt('ticket')

    def test_raises_invalid_ticket_error(self, request):
        request.return_value = self.invalid_ticket

        with pytest.raises(InvalidTicketError):
            self.c.uma_rp_get_rpt('ticket')

    def test_raises_need_info_error(self, request):
        request.return_value = self.needs_info

        with pytest.raises(NeedInfoError):
            self.c.uma_rp_get_rpt('ticket')


@patch.object(Messenger, 'request')
class UmaRsProtectTestCase(unittest.TestCase):
    def setUp(self):
        self.success = { "status":"ok"}
        self.c = Client(uma_config)

    def test_command(self, request):
        request.return_value = self.success

        resources = [{"path": "/photo",
                      "conditions": [{
                          "httpMethods": ["GET"],
                          "scopes": ["http://photoz.example.com/dev/actions/view"]
                          }]
                      }]

        assert self.c.uma_rs_protect(resources)

    def test_raises_error_on_oxd_server_error(self, request):
        request.return_value = generic_error

        with pytest.raises(OxdServerError):
            self.c.uma_rs_protect([])


@patch.object(Messenger, 'request')
class UmaRsCheckAccessTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status":"ok",
            "data": {"access":"granted"}
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
            "status":"ok",
            "data": {
                "access":"denied"
            }
        }
        self.failure = {
            "status": "error",
            "data": {
                "error":"invalid_request",
                "error_description":"Resource is not protected. Please protect your resource first with uma_rs_protect command."
            }
        }
        self.c = Client(uma_config)

    def test_returns_access_dict(self, request):
        request.return_value = self.success

        response = self.c.uma_rs_check_access('rpt', '/photoz', 'GET')
        assert response["access"] == "granted"

        assert 'oxd_id' in request.call_args[1]
        assert 'rpt' in request.call_args[1]
        assert 'path' in request.call_args[1]
        assert 'http_method' in request.call_args[1]

    def test_raises_error_on_oxd_server_error(self, request):
        request.return_value = self.failure

        with pytest.raises(OxdServerError):
            self.c.uma_rs_check_access('rpt', '/photoz', 'GET')

@patch.object(Messenger, 'request')
class UmaRpGetClaimsGatherUrlTestCase(unittest.TestCase):
    def test_command(self, request):
        request.return_value = {
            "status": "ok",
            "data": { "url": "https://as.com/restv1/uma/gather_claims"}
        }
        c = Client(uma_config)
        c.uma_rp_get_claims_gathering_url('ticket')
        assert 'oxd_id' in request.call_args[1]
        assert 'ticket' in request.call_args[1]
        assert 'claims_redirect_uri' in request.call_args[1]

    def test_raises_error_on_oxd_server_error(self, request):
        request.return_value = generic_error
        c = Client(uma_config)
        with pytest.raises(OxdServerError):
            c.uma_rp_get_claims_gathering_url('ticket')


@patch.object(Messenger, 'request')
class SetupClientTestCase(unittest.TestCase):
    @patch.object(Configurer, 'set')
    def test_command(self, mock_set, request):
        request.return_value = {
            "status":"ok",
            "data":{
                "oxd_id":"6F9619FF-8B86-D011-B42D-00CF4FC964FF",
                "op_host": "<op host>",
                "client_id": "<client id>",
                "client_secret": "<client secret>",
                "client_registration_access_token": "<Client registration access token>",
                "client_registration_client_uri": "<URI of client registration>",
                "client_id_issued_at": "<client_id issued at>",
                "client_secret_expires_at": "<client_secret expires at>"
            }
        }

        c = Client(initial_config)
        assert c.setup_client()
        assert "authorization_redirect_uri" in request.call_args[1]
        assert "post_logout_redirect_uri" in request.call_args[1]
        assert "client_frontchannel_logout_uris" in request.call_args[1]

        mock_set.assert_any_call("client", "client_id", "<client id>")
        mock_set.assert_any_call("client", "client_secret", "<client secret>")
        mock_set.assert_any_call(
            "client", "client_registration_access_token",
            "<Client registration access token>"
        )

    def test_raises_error_when_oxd_server_errors(self, request):
        request.return_value = generic_error

        c = Client(initial_config)
        with pytest.raises(OxdServerError):
            c.setup_client()


@patch.object(Messenger, 'request')
class GetClientTokenTestCase(unittest.TestCase):
    def setUp(self):
        self.success = {
            "status":"ok",
            "data": {
                "access_token": "6F9619FF-8B86-D011-B42D-00CF4FC964FF",
                "expires_in": 399,
                "refresh_token": "fr459f",
                "scope": "openid"
            }
        }

    def test_command(self, request):
        request.return_value = self.success

        c = Client(https_config)
        token = c.get_client_token()['access_token']
        assert token == "6F9619FF-8B86-D011-B42D-00CF4FC964FF"

        assert "client_id" in request.call_args[1]
        assert "client_secret" in request.call_args[1]
        assert "op_host" in request.call_args[1]

    def test_override_of_client_credentials(self, request):
        request.return_value = self.success

        c = Client(https_config)
        # Override value of client_id, client_secret and op_host
        c.get_client_token('client-id', 'client-secret', 'new-host')
        assert request.call_args[1]["client_id"] == 'client-id'
        assert request.call_args[1]["client_secret"] == 'client-secret'
        assert request.call_args[1]["op_host"] == 'new-host'

        # add optional arguments op_discovery_path and scope
        assert c.get_client_token('client-id', 'client-secret', 'new_host',
                                  'https://mag.el/lan', ['openid', 'profile'])
        assert request.call_args[1]['op_discovery_path'] == 'https://mag.el/lan'
        assert request.call_args[1]['scope'] == ['openid', 'profile']

    def test_throws_error_on_oxd_server_error(self, request):
        request.return_value = generic_error

        c = Client(https_config)
        with pytest.raises(OxdServerError):
            c.get_client_token()
