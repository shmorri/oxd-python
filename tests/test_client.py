import os
import unittest
from mock import patch
from nose.tools import assert_equal, assert_is_instance, assert_true, assert_false,\
    assert_raises, assert_is_none, assert_is_not_none, assert_in, \
    assert_not_equal

from oxdpython import Client
from oxdpython.messenger import Messenger

this_dir = os.path.dirname(os.path.realpath(__file__))
config_location = os.path.join(this_dir, 'data', 'initial.cfg')
uma_config = os.path.join(this_dir, 'data', 'umaclient.cfg')

class ClientTest(unittest.TestCase):

    def test_initializes_with_config(self):
        c = Client(config_location)
        assert_equal(c.config.get('oxd', 'connection_type_value'), '8099')
        #assert_is_instance(c.msgr, Messenger)
        assert_equal(c.authorization_redirect_uri,"https://client.example.com:8080/userinfo")


    def test_register_site_command(self):
        # preset register client command response
        config = os.path.join(this_dir, 'data', 'register_site_test.cfg')
        oxc = Client(config)
        #oxc = Client(config_location)
        oxc.oxd_id = None
        assert_is_none(oxc.oxd_id)
        response = oxc.get_client_token()
        protection_access_token = str(response.access_token)
        assert_is_not_none(protection_access_token)
        oxc.register_site(protection_access_token)
        assert_is_not_none(oxc.oxd_id)


    def test_setup_client_command(self):
        # preset setup client command response
        oxc = Client(config_location)
        oxc.oxd_id = None

        assert_is_none(oxc.oxd_id)
        assert_false(oxc.config.get("client", "client_id"))
        assert_false(oxc.config.get("client", "client_secret"))
        oxc.setup_client()
        assert_is_not_none(oxc.oxd_id)
        assert_is_not_none(oxc.config.get('client', 'client_id'))
        assert_is_not_none(oxc.config.get('client', 'client_secret'))


    def test_setup_client_command_for_http_extension(self):
        # preset setup client command response
        config = os.path.join(this_dir, 'data', 'initial_web.cfg')
        oxc = Client(config)
        oxc.oxd_id = None

        assert_is_none(oxc.oxd_id)
        assert_false(oxc.config.get("client", "client_id"))
        assert_false(oxc.config.get("client", "client_secret"))
        oxc.setup_client()
        assert_is_not_none(oxc.oxd_id)
        assert_is_not_none(oxc.config.get('client', 'client_id'))
        assert_is_not_none(oxc.config.get('client', 'client_secret'))


    def test_setup_raises_runtime_error_for_oxd_error_response(self):
        config = os.path.join(this_dir, 'data', 'no_oxdid.cfg')
        oxc = Client(config)
        with assert_raises(RuntimeError):
            oxc.setup_client()

    @unittest.skip("WIP")
    @patch.object(Messenger, 'send')
    def test_get_client_token(self, mock_send):
        oxc = Client(config_location)
        mock_send.return_value.status = "ok"
        mock_send.return_value.data = "access-token"
        command = {"command": "get_client_token"}
        params = {
            "client_id": oxc.client_id,
            "client_secret": oxc.client_secret,
            "op_host": oxc.config.get("client", "op_host")
            }

        command["params"] = params

        protection_access_token = oxc.get_client_token()
        mock_send.assert_called_with(command)

        assert_equal(protection_access_token, "access-token")

    @patch.object(Messenger, 'sendtohttp')
    def test_get_client_token_for_http_extension(self, mock_sendtohttp):
        config = os.path.join(this_dir, 'data', 'initial_web.cfg')
        oxc = Client(config)
        mock_sendtohttp.return_value.status = "ok"
        mock_sendtohttp.return_value.data = "access-token"
        rest_url = oxc.conn_type_value + "get-client-token"
        params = {
            "client_id": oxc.client_id,
            "client_secret": oxc.client_secret,
            "op_host": oxc.config.get("client", "op_host")
        }

        protection_access_token = oxc.get_client_token()
        mock_sendtohttp.assert_called_with(params,rest_url)

        assert_equal(protection_access_token, "access-token")



    def test_get_authorization_url(self):
        oxc = Client(config_location)
        auth_url = oxc.get_authorization_url()
        assert_in('userinfo', auth_url)


    def test_get_authorization_url_for_http_extension(self):
        config = os.path.join(this_dir, 'data', 'initial_web.cfg')
        oxc = Client(config)

        if oxc.config.get("client", "dynamic_registration") == 'true' and oxc.config.get("oxd", "connection_type") == 'web':
            response = oxc.get_client_token()
            print response
            protection_access_token = str(response.access_token)
            assert_true(protection_access_token)
            auth_url = oxc.get_authorization_url(protection_access_token=protection_access_token)
            print auth_url
            assert_in('userinfo', auth_url)



    @unittest.skip("WIP")
    def test_get_authorization_url_works_wihtout_explicit_site_registration(self):
        oxc = Client(config_location)
        oxc.oxd_id = None  # assume the client isn't registered
        auth_url = oxc.get_authorization_url()
        assert_in('userinfo', auth_url)

    def test_get_auth_url_accepts_optional_params(self):
        oxc= Client(config_location)
        if oxc.config.get("client", "dynamic_registration") == 'true' and oxc.config.get("oxd", "connection_type") == 'web':
            response = oxc.get_client_token()
            print response
            protection_access_token = str(response.access_token)
            assert_true(protection_access_token)
        else:
            protection_access_token = ''

        #acr values
        auth_url = oxc.get_authorization_url(protection_access_token=protection_access_token,acr_values=["basic"])
        assert_in('basic', auth_url)

        # prompt
        auth_url = oxc.get_authorization_url(protection_access_token=protection_access_token, acr_values=["basic"], prompt="login")
        assert_in('basic', auth_url)
        assert_in('prompt', auth_url)

        # scope
        auth_url = oxc.get_authorization_url(protection_access_token=protection_access_token, acr_values=["basic"], prompt=None,
                                           scope=["openid", "profile", "email"])
        assert_in('openid', auth_url)
        assert_in('profile', auth_url)
        assert_in('email', auth_url)

    @patch.object(Messenger, 'send')
    def test_get_tokens_by_code_without_pat(self, mock_send):
        oxc = Client(config_location)

        code = "code"
        state = "state"

        command = {"command": "get_tokens_by_code"}

        params = {"oxd_id": oxc.oxd_id,
                  "code": code,
                  "state": state,
                  }

        command["params"] = params

        if(oxc.config.get("client", "protect_commands_with_access_token") == 'false'):
            mock_send.return_value.status = "ok"
            mock_send.return_value.data = "mock-token"
            token = oxc.get_tokens_by_code(code=code, state=state)
            mock_send.assert_called_with(command)
            assert_equal(token, "mock-token")

        elif(oxc.config.get("client", "protect_commands_with_access_token") == 'true'):
            mock_send.return_value.status = "error"
            mock_send.return_value.data.error = "blank_protection_access_token"
            with assert_raises(RuntimeError):
                oxc.get_tokens_by_code("code", "state")



    @patch.object(Messenger, 'sendtohttp')
    def test_get_tokens_by_code__for_http_extension(self, mock_sendtohttp):
        config = os.path.join(this_dir, 'data', 'initial_web.cfg')
        oxc = Client(config)

        protection_access_token = "access-token"

        code = "code"
        state = "state"

        rest_url = oxc.conn_type_value + "get-tokens-by-code"

        params = {"oxd_id": oxc.oxd_id,
                      "code": code,
                      "state": state,
                      }

        if protection_access_token and isinstance(protection_access_token, str):
            params["protection_access_token"] = protection_access_token

        mock_sendtohttp.return_value.status = "ok"
        mock_sendtohttp.return_value.data = "mock-token"
        token = oxc.get_tokens_by_code(code=code, state=state, protection_access_token=protection_access_token)
        mock_sendtohttp.assert_called_with(params, rest_url)
        assert_equal(token, "mock-token")

    @patch.object(Messenger, 'send')
    def test_get_tokens_raises_error_if_response_has_error(self,mock_send):
        oxc = Client(config_location)
        mock_send.return_value.status = "error"
        mock_send.return_value.data.error = "MockError"
        mock_send.return_value.data.error_description = "No Tokens in Mock"

        with assert_raises(RuntimeError):
            oxc.get_tokens_by_code("code", "state")


    @patch.object(Messenger, 'send')
    def test_get_user_info_without_pat(self,mock_send):
        oxc = Client(config_location)
        token = "tokken"
        command = {"command": "get_user_info",
                   "params": {
                       "oxd_id": oxc.oxd_id,
                       "access_token": token
                       }}

        if (oxc.config.get("client", "protect_commands_with_access_token") == 'false'):
            mock_send.return_value.status = "ok"
            mock_send.return_value.data.claims = {"name": "mocky"}
            claims = oxc.get_user_info(access_token=token)
            mock_send.assert_called_with(command)
            # assert_equal(token, "mock-token")
            assert_equal(claims, {"name": "mocky"})

        elif (oxc.config.get("client", "protect_commands_with_access_token") == 'true'):
            mock_send.return_value.status = "error"
            mock_send.return_value.data.error = "blank_protection_access_token"
            with assert_raises(RuntimeError):
                oxc.get_user_info(access_token=token)


    @patch.object(Messenger, 'sendtohttp')
    def test_get_user_info_with_pat_for_http_extension(self, mock_sendtohttp):
        config = os.path.join(this_dir, 'data', 'initial_web.cfg')
        oxc = Client(config)

        protection_access_token = "access-token"

        token = "tokken"
        rest_url = oxc.conn_type_value + "get-user-info"
        params = {
            "oxd_id": oxc.oxd_id,
            "access_token": token
        }

        if protection_access_token and isinstance(protection_access_token, str):
            params["protection_access_token"] = protection_access_token

        mock_sendtohttp.return_value.status = "ok"
        mock_sendtohttp.return_value.data.claims = {"name": "mocky"}
        claims = oxc.get_user_info(access_token=token, protection_access_token=protection_access_token)
        mock_sendtohttp.assert_called_with(params, rest_url)
        # assert_equal(token, "mock-token")
        assert_equal(claims, {"name": "mocky"})


    def test_get_user_info_raises_erro_on_invalid_args(self):
        oxc = Client(config_location)
        # Empty code should raise error
        with assert_raises(RuntimeError):
            oxc.get_user_info("")


    @patch.object(Messenger, 'send')
    def test_get_user_info_raises_error_on_oxd_error(self,mock_send):
        oxc = Client(config_location)
        mock_send.return_value.status = "error"
        mock_send.return_value.data.error = "MockError"
        mock_send.return_value.data.error_description = "No Claims for mock"

        with assert_raises(RuntimeError):
            oxc.get_user_info("some_token")

    @patch.object(Messenger, 'send')
    def test_logout_without_pat(self, mock_send):
        oxc = Client(config_location)

        mock_send.return_value.status = "ok"
        mock_send.return_value.data.uri = "https://example.com/end_session"

        params = {"oxd_id": oxc.oxd_id}

        command = {"command": "get_logout_uri",
                   "params": params}

        if (oxc.config.get("client", "protect_commands_with_access_token") == 'false'):
            # called without optional params
            uri = oxc.get_logout_uri()
            mock_send.assert_called_with(command)

            # called with OPTIONAL id_token_hint
            uri = oxc.get_logout_uri(id_token_hint="some_id")
            command["params"]["id_token_hint"] = "some_id"
            mock_send.assert_called_with(command)
            assert_equal(uri, "https://example.com/end_session")

            # called with OPTIONAL id_token_hint + post_logout_redirect_uri
            uri = oxc.get_logout_uri(id_token_hint="some_id", post_logout_redirect_uri="https://some.site/logout")
            command["params"]["post_logout_redirect_uri"] = "https://some.site/logout"
            mock_send.assert_called_with(command)

            # called with OPTIONAL id_token_hint + post_logout_redirect_uri + state
            uri = oxc.get_logout_uri(id_token_hint="some_id", post_logout_redirect_uri="https://some.site/logout",
                                   state="some-s")
            command["params"]["state"] = "some-s"
            mock_send.assert_called_with(command)

            # called with OPTIONAL id_token_hint + post_logout_redirect_uri + state + session_state
            uri = oxc.get_logout_uri(id_token_hint="some_id", post_logout_redirect_uri="https://some.site/logout",
                                   state="some-s",
                                   session_state="some-ss")
            command["params"]["session_state"] = "some-ss"
            mock_send.assert_called_with(command)

        elif (oxc.config.get("client", "protect_commands_with_access_token") == 'true'):
            mock_send.return_value.status = "error"
            mock_send.return_value.data.error = "blank_protection_access_token"
            with assert_raises(RuntimeError):
                oxc.get_logout_uri()


    @patch.object(Messenger, 'sendtohttp')
    def test_logout_with_pat_for_http_extension(self, mock_sendtohttp):
        config = os.path.join(this_dir, 'data', 'initial_web.cfg')
        oxc = Client(config)

        protection_access_token = "access-token"

        params = {"oxd_id": oxc.oxd_id}

        if protection_access_token and isinstance(protection_access_token, str):
            params["protection_access_token"] = protection_access_token

        rest_url = oxc.conn_type_value + "get-logout-uri"

        mock_sendtohttp.return_value.status = "ok"
        mock_sendtohttp.return_value.data.uri = "https://example.com/end_session"

        # called with protection_access_token
        uri = oxc.get_logout_uri(protection_access_token=protection_access_token)
        params["protection_access_token"] = protection_access_token
        mock_sendtohttp.assert_called_with(params,rest_url)

        # called with OPTIONAL id_token_hint
        uri = oxc.get_logout_uri(id_token_hint="some_id", protection_access_token=protection_access_token)
        params["id_token_hint"] = "some_id"
        mock_sendtohttp.assert_called_with(params,rest_url)
        assert_equal(uri, "https://example.com/end_session")

        # called with OPTIONAL id_token_hint + post_logout_redirect_uri
        uri = oxc.get_logout_uri(id_token_hint="some_id", post_logout_redirect_uri="https://some.site/logout",
                               protection_access_token=protection_access_token)
        params["post_logout_redirect_uri"] = "https://some.site/logout"
        mock_sendtohttp.assert_called_with(params,rest_url)

        # called with OPTIONAL id_token_hint + post_logout_redirect_uri + state
        uri = oxc.get_logout_uri(id_token_hint="some_id", post_logout_redirect_uri="https://some.site/logout",
                               state="some-s", protection_access_token=protection_access_token)
        params["state"] = "some-s"
        mock_sendtohttp.assert_called_with(params,rest_url)

        # called with OPTIONAL id_token_hint + post_logout_redirect_uri + state + session_state
        uri = oxc.get_logout_uri(id_token_hint="some_id", post_logout_redirect_uri="https://some.site/logout",
                               state="some-s",
                               session_state="some-ss", protection_access_token=protection_access_token)
        params["session_state"] = "some-ss"
        mock_sendtohttp.assert_called_with(params, rest_url)

    @patch.object(Messenger, 'send')
    def test_logout_raises_error_when_oxd_return_error(self,mock_send):
        oxc = Client(config_location)
        mock_send.return_value.status = "error"
        mock_send.return_value.data.error = "MockError"
        mock_send.return_value.data.error_description = "Logout Mock Error"

        with assert_raises(RuntimeError):
            oxc.get_logout_uri()


    def test_update_site_registration(self):
        oxc = Client(config_location)
        oxc.config.set('client', 'post_logout_redirect_uri',
                     'https://client.example.com/')
        status = oxc.update_site_registration()
        assert_true(status)

    def test_update_site_registration_for_http_extension(self):
        config = os.path.join(this_dir, 'data', 'initial_web.cfg')
        oxc = Client(config)
        response = oxc.get_client_token()
        protection_access_token = str(response.access_token)
        assert_is_not_none(protection_access_token)
        oxc.config.set('client', 'post_logout_redirect_uri',
                     'https://client.example.com/')
        status = oxc.update_site_registration(protection_access_token)
        assert_true(status)

    @unittest.skip("WIP")
    def test_delete_config(self):
        oxc = Client(config_location)
        oxc.delete_config()
        assert_false(oxc.config.get("oxd" , "id"))
        print oxc.authorization_redirect_uri
        assert_false(oxc.config.get("client" , "authorization_redirect_uri"))