import logging
import urllib2
import ssl
from .configurer import Configurer
from .messenger import Messenger


LOGGER = logging.getLogger(__name__)


class Client:

    def __init__(self, config_location):
        """Constructor for the Client class"""
        self.config = Configurer(config_location)

        self.conn_type = self.config.get("oxd", "connection_type")
        self.conn_type_value = self.config.get("oxd", "connection_type_value")

        if self.conn_type == "web" and self.conn_type_value[-1:] != "/":
            self.conn_type_value += "/"

        self.oxd_id = self.config.get("oxd", "id")
        self.client_name = self.config.get("client", "client_name")
        self.client_id = self.config.get("client", "client_id")
        self.client_secret = self.config.get("client", "client_secret")
        self.op_host = self.config.get("client", "op_host")
        self.ophost_type = None

        #list of optional params that can be passed to the oxd-server
        self.opt_params = ["op_host",
                           "post_logout_redirect_uri",
                           "client_name",
                           "client_jwks_uri",
                           "client_token_endpoint_auth_method",
                           "client_id",
                           "client_secret",
                           "client_secret_expires_at",
                           "application_type"]
        self.opt_list_params = ["grant_types",
                                "acr_values",
                                "contacts",
                                "client_frontchannel_logout_uris",
                                "client_request_uris",
                                "client_sector_identifier_uri",
                                "response_types",
                                "scope",
                                "ui_locales",
                                "claims_locales",
                               ]

    @staticmethod
    def __clear_data(response):
        """A private method that verifies that the oxd response is error free
        and raises a RuntimeError when it encounters an error
        """
        if response.status == "error":
            error = "oxd Server Error: {0}\nDescription:{1}".format(
                response.data.error, response.data.error_description)
            LOGGER.error(error)
            raise RuntimeError(error)
        elif response.status == "ok":
            return response.data

    def get_config_value(self):
        """A private method which returns the client attributes"""
        return {"op_host":self.config.get("client", "op_host"),
                "client_name":self.config.get("client", "client_name"),
                "authorization_redirect_url":self.config.get("client", "authorization_redirect_uri"),
                "post_logout_redirect_uri":self.config.get("client", "post_logout_redirect_uri"),
                "connection_type_value":self.config.get("oxd", "connection_type_value"),
                "id":self.config.get("oxd", "id"),
                "client_id":self.config.get("client", "client_id"),
                "client_secret":self.config.get("client", "client_secret"),
                "connection_type":self.config.get("oxd", "connection_type"),
                "dynamic_registration":self.config.get("client", "dynamic_registration")
               }

    def set_config_value(self, values):
        """A private method which sets the client attributes"""
        self.config.set("client", "op_host", values[0])
        self.config.set("client", "client_name", values[1])
        self.config.set("client", "authorization_redirect_uri", values[2])
        self.config.set("client", "post_logout_redirect_uri", values[3])
        self.config.set("oxd", "connection_type_value", values[4])
        self.config.set("oxd", "connection_type", values[5])

        return

    def openid_type(self, op_host):
        """Fucntion to know static or dynamic openID Provider.
        This should be called after getting the URI of the OpenID Provider, Client Redirect URI, Post logout URI, oxd port values from user.
        Returns:
            bool: The type for openID Provider type. True for dynamic and False for static openID provider.
        """
        op_host = op_host + "/.well-known/openid-configuration"

        try:
            res = urllib2.urlopen(op_host)
        except urllib2.URLError, e:
            if "[SSL: CERTIFICATE_VERIFY_FAILED]" in str(e.reason):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                res = urllib2.urlopen(op_host, context=ctx)
            else:
                raise e

        data = res.read()
        if "registration_endpoint" in data:
            #dynamic
            self.ophost_type = "dynamic"
            return True
        else:
            #static
            self.ophost_type = "static"
            return False

    def register_site(self, protection_access_token):
        """Function to register the site and generate a unique ID for the site

        Returns:
            string: The ID of the site (also called client id) if the
            registration is sucessful

        Raises:
            RuntimeError: If the site registration fails.
        """
        if self.oxd_id:
            LOGGER.info('Client is already registered. ID: %s', self.oxd_id)
            return self.oxd_id

        if self.conn_type == "web" and self.conn_type_value[-1:] != "/":
            self.conn_type_value += "/"

        command = {"command": "register_site"}
        rest_url = self.conn_type_value + "register-site"


        # add required params for the command
        params = {
            "authorization_redirect_uri": self.config.get("client", "authorization_redirect_uri"),
            "protection_access_token": protection_access_token

        }
        # add other optional params if they exist in config
        for param in self.opt_params:
            if self.config.get("client", param):
                value = self.config.get("client", param)
                params[param] = value

        for param in self.opt_list_params:
            if self.config.get("client", param):
                value = self.config.get("client", param).split(",")
                params[param] = value

        command["params"] = params
        LOGGER.debug("Sending command `register_site` with params %s",
                     params)

        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)


        LOGGER.debug("Recieved reponse: %s", response)

        self.oxd_id = self.__clear_data(response).oxd_id
        self.config.set("oxd", "id", self.oxd_id)
        LOGGER.info("Site registration successful. oxd ID: %s", self.oxd_id)
        return self.oxd_id


    def setup_client(self, op_host, client_name, authorization_redirect_uri, post_logout_uri, clientId, clientSecret, conn_type, conn_type_value, claims_redirect_uri):
        """Function to setup the client and generate a Client ID, Client Secret for the site

        Returns:
            NamedTuple: The tokens object with the following data structure::

                {
                    "oxd_id": "<token string>",
                    "op_host": "<token string>",
                    "client_id": "<token string>",
                    "client_secret": "<token string>",
                    "client_registration_access_token": "<token string>",
                    "client_registration_client_uri": "<token string>",
                    "client_id_issued_at": "<token long>",
                    "client_secret_expires_at": "<token long>"
                }

            Since this would be returned as a NamedTuple, it can be accessed
            using the dot notation as :obj:`data.oxd_id`,
            :obj:`data.client_id`, :obj:`data.client_secret`...etc.,

        Raises:
            RuntimeError: If the site client setup fails.
        """
        values = [op_host, client_name, authorization_redirect_uri, post_logout_uri, conn_type_value, conn_type]

        self.set_config_value(values)
        self.config.set("client", "client_id", clientId)
        self.config.set("client", "client_secret", clientSecret)

        if conn_type == "web" and conn_type_value[-1:] != "/":
            conn_type_value += "/"

        command = {"command": "setup_client"}
        rest_url = conn_type_value + "setup-client"


        # add required params for the command
        params = {"authorization_redirect_uri": authorization_redirect_uri,
                  "op_host": op_host,
                  "post_logout_redirect_uri": post_logout_uri,
                  "client_id": clientId,
                  "client_secret": clientSecret,
                  "oxd_rp_programming_language": 'python',
                  "claims_redirect_uri": claims_redirect_uri,}

        # add other optional params if they exist in config
        for param in self.opt_params:
            if self.config.get("client", param):
                value = self.config.get("client", param)
                params[param] = value

        for param in self.opt_list_params:
            if self.config.get("client", param):
                value = self.config.get("client", param).split(",")
                params[param] = value

        command["params"] = params
        LOGGER.debug("Sending command `setup_client` with params %s",
                     params)

        if conn_type == "local":
            msgr = Messenger(int(conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)

        LOGGER.debug("Recieved reponse: %s", response)

        self.oxd_id = self.__clear_data(response).oxd_id
        clientid = self.__clear_data(response).client_id
        clientsecret = self.__clear_data(response).client_secret
        if self.oxd_id and clientid and clientsecret:
            self.config.set("oxd", "id", self.oxd_id)
            self.config.set("client", "client_id", clientid)
            self.config.set("client", "client_secret", clientsecret)

        LOGGER.info("Setup Client successful. oxd ID: %s, Client ID: %s", self.oxd_id,
                    self.__clear_data(response).client_id)

        return self.__clear_data(response)


    def update_site_registration(self, protection_access_token, client_name, authorization_redirect_uri, post_logout_uri, connection_type_value, connection_type):
        """Fucntion to update the site's information with OpenID Provider.
        This should be called after changing the values in the cfg file.
        Returns:
            bool: The status for update. True for success and False for failure
        """
        command = {"command": "update_site_registration"}
        rest_url = self.conn_type_value + "update-site"


        params = {"oxd_id": self.oxd_id,
                  "protection_access_token": protection_access_token,
                  "authorization_redirect_uri": authorization_redirect_uri,
                  "post_logout_redirect_uri": post_logout_uri,
                 }

        # add other optional params if they exist in config
        for param in self.opt_params:
            if self.config.get("client", param):
                value = self.config.get("client", param)
                params[param] = value

        for param in self.opt_list_params:
            if self.config.get("client", param):
                value = self.config.get("client", param).split(",")
                params[param] = value

        command["params"] = params
        LOGGER.debug("Sending `update_site_registration` with params %s", params)


        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)

        LOGGER.debug("Recieved reponse: %s", response)
        if response.status == 'ok':
            values = [self.config.get("client", "op_host"), client_name, authorization_redirect_uri, post_logout_uri, connection_type_value, connection_type]
            self.set_config_value(values)

        return response.status

    def delete_config(self):
        """A private method which deletes client attributes from the config file"""
        self.config.set("oxd", "id", '')
        self.config.set("client", "dynamic_registration", '')
        self.set_config_value(['', '', '', '', '', ''])
        self.config.set("client", "client_id", '')
        self.config.set("client", "client_secret", '')

    def get_authorization_url(self, protection_access_token, acr_values=None, prompt=None, scope=None):
        """Function to get the authorization url that can be opened in the
        browser for the user to provide authorization and authentication

        Args:
            acr_values (list, optional): acr values in the order of priority
            prompt (string, optional): prompt=login is required if you want to
                force alter current user session (in case user is already
                logged in from site1 and site2 construsts authorization
                request and want to force alter current user session)
            scope (list, optional): scopes required, takes the one provided
                during site registrations by default

        Returns:
            string: The authorization url that the user must access for
            authentication and authorization

        Raises:
            RuntimeError: If the oxd throws an error for any reason.
        """
        command = {"command": "get_authorization_url"}
        rest_url = self.conn_type_value + "get-authorization-url"

        params = {"oxd_id": self.oxd_id,
                  "protection_access_token": protection_access_token,
                 }

        if scope and isinstance(scope, list):
            params["scope"] = scope

        if acr_values and isinstance(acr_values, list):
            params["acr_values"] = acr_values

        if prompt and isinstance(prompt, str):
            params["prompt"] = prompt

        command["params"] = params
        LOGGER.debug("Sending command `get_authorization_url` with params %s", params)

        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)

        LOGGER.debug("Recieved reponse: %s", response)

        return self.__clear_data(response).authorization_url


    def get_tokens_by_code(self, protection_access_token, code, state):
        """Function to get access code for getting the user details from the
        OP. It is called after the user authorizies by visiting the auth URL.

        Args:
            code (string): code, parse from the callback URL querystring
            state (string): state value parsed from the callback URL

        Returns:
            NamedTuple: The tokens object with the following data structure::

                {
                    "access_token": "<token string>",
                    "expires_in": 3600,
                    "refresh_token": "<token string>",
                    "id_token": "<token string>",
                    "id_token_claims":
                    {
                        "iss": "https://server.example.com",
                        "sub": "24400320",
                        "aud": "s6BhdRkqt3",
                        "nonce": "n-0S6_WzA2Mj",
                        "exp": 1311281970,
                        "iat": 1311280970,
                        "at_hash": "MTIzNDU2Nzg5MDEyMzQ1Ng"
                    }
                }

            Since this would be returned as a NamedTuple, it can be accessed
            using the dot notation as :obj:`data.access_token`,
            :obj:`data.refresh_token`, :obj:`data.id_token`...etc.,

        Raises:
            RuntimeError: If oxd server throws an error OR if the params code
                and scopes are of improper datatype.
        """
        command = {"command": "get_tokens_by_code"}
        rest_url = self.conn_type_value + "get-tokens-by-code"


        params = {"oxd_id": self.oxd_id,
                  "protection_access_token": protection_access_token,
                  "code": code,
                  "state": state
                 }

        command["params"] = params
        LOGGER.debug("Sending command `get_tokens_by_code` with params %s", params)

        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)

        LOGGER.debug("Recieved response: %s", response)

        return self.__clear_data(response)

    def get_access_token_by_refresh_token(self, protection_access_token, refresh_token, scope=None):
        """Function to get access code for getting the user details from the
                        OP by using the refresh_token.
                        It is called after getting the refresh_token by using the code and state.

                        Args:
                            refresh_token (string): refresh_token is obtained by using the code and state
                            scope (list, optional): scopes required, takes the one provided
                                during site registrations by default

                        Returns:
                            NamedTuple: The tokens object with the following data structure::

                                {
                                    "status":"ok",
                                    "data":{
                                        "access_token":"SlAV32hkKG",
                                        "expires_in":3600,
                                        "refresh_token":"aaAV32hkKG1"
                                    }
                                }

                            Since this would be returned as a NamedTuple, it can be accessed
                            using the dot notation as :obj:`data.access_token`,
                            :obj:`data.refresh_token`, :obj:`data.id_token`...etc.,

                        Raises:
                            RuntimeError: If oxd server throws an error OR if the params code
                                and scopes are of improper datatype.
                        """

        command = {"command": "get_access_token_by_refresh_token"}
        rest_url = self.conn_type_value + "get-access-token-by-refresh-token"

        params = {"oxd_id": self.oxd_id,
                  "protection_access_token": protection_access_token,
                  "refresh_token": refresh_token,
                 }

        if scope and isinstance(scope, list):
            params["scope"] = scope

        command["params"] = params
        LOGGER.debug("Sending command `get_access_token_by_refresh_token` with params %s", params)

        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)

        LOGGER.debug("Recieved response: %s", response)

        return self.__clear_data(response)

    def get_client_token(self):
        """A method which generates the protection access token"""
        command = {"command": "get_client_token"}
        rest_url = self.conn_type_value + "get-client-token"

        #add required params for the command
        params = {
            "client_id":  self.client_id,
            "client_secret":  self.client_secret,
            "op_host": self.op_host
        }

        command["params"] = params
        LOGGER.debug("Sending command `get_client_token` with params %s",
                     params)

        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)

        LOGGER.debug("Recieved reponse: %s", response)

        return_data = self.__clear_data(response)

        return return_data

    def get_user_info(self, protection_access_token, access_token):
        """Function to get the information about the user using the access code
        obtained from the OP

        Args:
            access_token (string): access token from the get_tokens_by_code
                                    function

        Returns:
            NamedTuple: The user data claims that are returned by the OP.
            Refer to the /.well-known/openid-configuration URL of your OP for
            the complete list of the claims for different scopes.

        Raises:
            RuntimeError: If the param access_token is empty OR if the oxd
                Server returns an error.
        """
        if not access_token:
            LOGGER.error("Empty access code sent for get_user_info")
            raise RuntimeError("Empty access code")

        command = {"command": "get_user_info"}
        rest_url = self.conn_type_value +"get-user-info"


        params = {"oxd_id": self.oxd_id,
                  "protection_access_token": protection_access_token,
                  "access_token": access_token
                 }

        command["params"] = params
        LOGGER.debug("Sending command `get_user_info` with params %s", params)

        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)

        LOGGER.debug("Recieved reponse: %s", response)

        return self.__clear_data(response).claims


    def get_logout_uri(self, protection_access_token, id_token_hint=None, post_logout_redirect_uri=None, state=None, session_state=None):
        """Function to logout the user.
        Args:
            id_token_hint (string, optional): oxd server will use last used
                ID Token, if not provided
            post_logout_redirect_uri (string, optional): URI to redirect,
                this uri would override the value given in the site-config
            state (string, optional): site state
            session_state (string, optional): session state

        Returns:
            string: The URI to which the user must be directed in order to
            perform the logout
        """

        command = {"command": "get_logout_uri"}
        rest_url = self.conn_type_value + "get-logout-uri"

        params = {"oxd_id": self.oxd_id,
                  "protection_access_token": protection_access_token
                 }


        if id_token_hint and isinstance(id_token_hint, str):
            params["id_token_hint"] = id_token_hint

        if post_logout_redirect_uri and isinstance(post_logout_redirect_uri, str):
            params["post_logout_redirect_uri"] = post_logout_redirect_uri

        if state and isinstance(state, str):
            params["state"] = state

        if session_state and isinstance(session_state, str):
            params["session_state"] = session_state


        command["params"] = params

        LOGGER.debug("Sending command `get_logout_uri` with params %s", params)

        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)

        LOGGER.debug("Recieved response: %s", response)

        return self.__clear_data(response).uri

    def uma_rs_protect(self, protection_access_token, resources):
        """Function to be used in a UMA Resource Server to protect resources.

        Args:
                    resources (list): list of resource to protect

        Returns:
                    bool: The status of the request.
        """

        command = {"command": "uma_rs_protect"}
        rest_url = self.conn_type_value + "uma-rs-protect"

        params = {"oxd_id": self.oxd_id,
                  "protection_access_token": protection_access_token,
                  "resources": resources
                 }

        if len(resources) < 1:
            return False

        params["resources"] = resources
        command["params"] = params

        LOGGER.debug("Sending `uma_rs_protect` with params %s", params)
        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)
        LOGGER.debug("Recieved response: %s", response)

        return self.__clear_data(response)

    def uma_rs_check_access(self, protection_access_token, rpt, path, http_method):
        """Function to be used in a UMA Resource Server to check access.

        Args:
            rpt (string): RPT or blank value if absent (not send by RP)
            path (string): Path of resource (e.g. for http://rs.com/phones,
                /phones should be passed)
            http_method (string) - Http method of RP request (GET, POST, PUT,
                DELETE)

        Returns:
            NamedTuple: The access information recieved in the format below.
            If the access is granted::

                { "access": "granted" }

            If the access is denied with ticket response::

                {
                    "access": "denied",
                    "www-authenticate_header": "UMA realm='example',
                        as_uri='https://as.example.com',
                        error='insufficient_scope',
                        ticket='016f84e8-f9b9-11e0-bd6f-0021cc6004de'",
                    "ticket": "016f84e8-f9b9-11e0-bd6f-0021cc6004de"
                }

            If the access is denied without ticket response::

                { "access": "denied" }

            If the resource is not Protected::

                {
                    "error": "invalid_request",
                    "error_description": "Resource is not protected. Please
                        protect your resource first with uma_rs_protect
                        command."
                }

        """

        command = {"command": "uma_rs_check_access"}
        rest_url = self.conn_type_value + "uma-rs-check-access"

        params = {"oxd_id": self.oxd_id,
                  "protection_access_token": protection_access_token,
                  "rpt": rpt,
                  "path": path,
                  "http_method": http_method
                 }

        command["params"] = params

        LOGGER.debug("Sending command `uma_rs_check_access` with params %s", params)
        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)
        LOGGER.debug("Received response: %s", response)

        return self.__clear_data(response)

    def uma_rp_get_rpt(self, protection_access_token, ticket, rpt=None, state=None, claim_token=None, claim_token_format=None, pct=None, scope=None):
        """Function to be used in a UMA Resource Server to get rpt.

                Args:
                    rpt (string): RPT or blank value if absent (not send by RP)
                    ticket(string): ticket value returned by the uma_rs_check_access() method

                Returns:
                    NamedTuple: The access information recieved in the format below.

                    Success Response:

                        {
                            "status":"ok",
                            "data":{
                                        "access_token":"SSJHBSUSSJHVhjsgvhsgvshgsv",
                                        "token_type":"Bearer",
                                        "pct":"c2F2ZWRjb25zZW50",
                                        "upgraded":true
                                    }
                        }

                    Needs info error response:

                        {
                            "status":"error",
                            "data":{
                            "error":"need_info",
                            "error_description":"The authorization server needs additional information in order to determine whether the client is authorized to have these permissions.",
                            "details": {
                                "error":"need_info",
                                "ticket":"ZXJyb3JfZGV0YWlscw==",
                            "required_claims":[
                                {
                                    "claim_token_format":[
                                    "http://openid.net/specs/openid-connect-core-1_0.html#IDToken"
                                ],
                                    "claim_type":"urn:oid:0.9.2342.19200300.100.1.3",
                                    "friendly_name":"email",
                                    "issuer":["https://example.com/idp"],
                                    "name":"email23423453ou453"
                                }
                            ],
                            "redirect_user":"https://as.example.com/rqp_claims?id=2346576421"
                         }
                    }
                }

                   Invalid ticket error:

                            {
                                "status":"error",
                                "data":{
                                    "error":"invalid_ticket",
                                    "error_description":"Ticket is not valid (outdated or not present on Authorization Server)."
                                    }
                            }

                    Internal oxd server error

                        {
                            "status":"error",
                            "data":{
                            "error":"internal_error",
                            "error_description":"oxd server failed to handle command. Please check logs for details."
                            }
                        }

                """

        command = {"command": "uma_rp_get_rpt"}
        rest_url = self.conn_type_value + "uma-rp-get-rpt"

        params = {"oxd_id": self.oxd_id,
                  "protection_access_token": protection_access_token,
                  "ticket": ticket,
                 }

        if claim_token and isinstance(claim_token, str):
            params["claim_token"] = claim_token

        if claim_token_format and isinstance(claim_token_format, str):
            params["claim_token_format"] = claim_token_format

        if pct and isinstance(pct, str):
            params["pct"] = pct

        if rpt and isinstance(rpt, str):
            params["rpt"] = rpt

        if scope and isinstance(scope, list):
            params["scope"] = scope

        if state and isinstance(state, str):
            params["state"] = state


        command["params"] = params

        LOGGER.debug("Sending command `uma_rs_check_access` with params %s", params)
        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)
        LOGGER.debug("Recieved response: %s", response)

        return self.__clear_data(response)

    def uma_rp_get_claims_gathering_url(self, protection_access_token, claims_redirect_uri, ticket):
        """Function to be used in a UMA Resource Server to obtain claims gathering url.

                Args:
                    claims_redirect_uri(string):
                    ticket(string): ticket value returned by the uma_rs_check_access() method

                Returns:
                    NamedTuple: The access information recieved in the format below.

                    {
                        "status":"ok",
                        "data":{
                                    "url":"https://as.com/restv1/uma/gather_claims
                                    ?client_id=@!1736.179E.AA60.16B2!0001!8F7C.B9AB!0008!AB77!1A2B
                                    &ticket=4678a107-e124-416c-af79-7807f3c31457
                                    &claims_redirect_uri=https://client.example.com/cb
                                    &state=af0ifjsldkj",
                                    "state":"af0ifjsldkj"
                                }
                    }"""

        command = {"command": "uma_rp_get_claims_gathering_url"}
        rest_url = self.conn_type_value + "uma-rp-get-claims-gathering-url"

        params = {"oxd_id": self.oxd_id,
                  "claims_redirect_uri": claims_redirect_uri,
                  "ticket": ticket,
                  "protection_access_token": protection_access_token,
                 }

        command["params"] = params

        LOGGER.debug("Sending command `uma_rs_check_access` with params %s",
                     params)
        if self.conn_type == "local":
            msgr = Messenger(int(self.conn_type_value))
            response = msgr.send(command)
        else:
            msgr = Messenger()
            response = msgr.sendtohttp(params, rest_url)
        LOGGER.debug("Recieved response: %s", response)

        return self.__clear_data(response)
