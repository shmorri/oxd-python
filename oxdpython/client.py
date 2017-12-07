import logging

from .configurer import Configurer
from .messenger import Messenger
from .exceptions import OxdServerError, NeedInfoError, InvalidTicketError

logger = logging.getLogger(__name__)


class Client:
    """Client is the main class that carries out the task of talking with the
    oxD server. The oxD commands are provided as class methods that are called
    to send the command to the oxD server via socket.
    """

    def __init__(self, config_location):
        """Constructor of class Client

        Args:
            config_location (string): The complete path of the location
                of the config file. Sample config at
                (https://github.com/GluuFederation/oxd-python/blob/master/sample.cfg)
        """
        self.oxd_id = None
        self.config = Configurer(config_location)
        if self.config.get("oxd", "https_extension"):
            logger.info("https_extenstion is enabled.")
            self.msgr = Messenger.create(self.config.get("oxd", "host"),
                                         https_extension=True)
        else:
            self.msgr = Messenger.create(self.config.get("oxd", "host"),
                                         int(self.config.get("oxd", "port")))

        if self.config.get("client", "protection_access_token"):
            logger.info("Protection Token available in config. Setting it to "
                        "messenger for use in all communication")
            self.msgr.access_token = self.config.get("client",
                                                     "protection_access_token")

        self.authorization_redirect_uri = self.config.get(
            "client", "authorization_redirect_uri")
        if self.config.get("oxd", "id"):
            self.oxd_id = self.config.get("oxd", "id")

            logger.info("Oxd ID found during initialization. Client is"
                        " already registered with the OpenID Provider")
            logger.info("oxd id: %s", self.oxd_id)

        # list of optional params that can be passed to the oxd-server
        self.opt_params = ["op_host",
                           "post_logout_redirect_uri",
                           "client_name",
                           "client_jwks_uri",
                           "client_token_endpoint_auth_method",
                           "client_id",
                           "client_secret",
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
                                "claims_redirect_uri",
                                ]

    def register_site(self):
        """Function to register the site and generate a unique ID for the site

        Returns:
            string: The ID of the site (also called client id) if the
            registration is successful

        Raises:
            OxdServerError: If the site registration fails.
        """
        if self.oxd_id:
            logger.info('Client is already registered. ID: %s', self.oxd_id)
            return self.oxd_id

        # add required params for the command
        params = {
            "authorization_redirect_uri": self.authorization_redirect_uri,
            }

        # add other optional params if they exist in config
        for op in self.opt_params:
            if self.config.get("client", op):
                params[op] = self.config.get("client", op)

        for olp in self.opt_list_params:
            if self.config.get("client", olp):
                params[olp] = self.config.get("client", olp).split(",")

        logger.debug("Sending command `register_site` with params %s", params)
        response = self.msgr.request("register_site", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])

        self.oxd_id = response["data"]["oxd_id"]
        self.config.set("oxd", "id", self.oxd_id)
        logger.info("Site registration successful. Oxd ID: %s", self.oxd_id)
        return self.oxd_id

    def get_authorization_url(self, acr_values=None, prompt=None, scope=None,
                              custom_params=None):
        """Function to get the authorization url that can be opened in the
        browser for the user to provide authorization and authentication

        Args:
            acr_values (list, optional): acr values in the order of priority
            prompt (string, optional): prompt=login is required if you want to
                force alter current user session (in case user is already
                logged in from site1 and site2 constructs authorization
                request and want to force alter current user session)
            scope (list, optional): scopes required, takes the one provided
                during site registrations by default
            custom_params (dict, optional): Any custom arguments that the
                client wishes to pass on to the OP can be passed on as extra
                parameters to the function

        Returns:
            string: The authorization url that the user must access for
            authentication and authorization

        Raises:
            OxdServerError: If the oxD throws an error for any reason.
        """
        if not self.oxd_id:
            self.register_site()

        params = {"oxd_id": self.oxd_id}

        if scope and isinstance(scope, list):
            params["scope"] = scope

        if acr_values and isinstance(acr_values, list):
            params["acr_values"] = acr_values

        if prompt and isinstance(prompt, str):
            params["prompt"] = prompt

        if custom_params:
            params["custom_parameters"] = custom_params

        logger.debug("Sending command `get_authorization_url` with params %s",
                     params)
        response = self.msgr.request("get_authorization_url", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])
        return response['data']['authorization_url']


    def get_tokens_by_code(self, code, state):
        """Function to get access code for getting the user details from the
        OP. It is called after the user authorizes by visiting the auth URL.

        Args:
            code (string): code, parse from the callback URL querystring
            state (string): state value parsed from the callback URL

        Returns:
            dict: The tokens object with the following data structure.

            Example response::

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

        Raises:
            OxdServerError: If oxD server throws an error OR if the params code
                and scopes are of improper data type.
        """
        params = dict(oxd_id=self.oxd_id, code=code, state=state)

        logger.debug("Sending command `get_tokens_by_code` with params %s",
                     params)
        response = self.msgr.request("get_tokens_by_code", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])
        return response['data']

    def get_access_token_by_refresh_token(self, refresh_token, scope=None):
        """Function that is used to get a new access token using refresh token

        Args:
            refresh_token (str): refresh_token from get_tokens_by_code command
            scope (list, optional): a list of scopes. If not specified should
                grant access with scope provided in previous request

        Returns:
            dict: the tokens with expiry time.

            Example response::

                {
                    "access_token":"SlAV32hkKG",
                    "expires_in":3600,
                    "refresh_token":"aaAV32hkKG1"
                }

        """
        params = {
            "oxd_id": self.oxd_id,
            "refresh_token": refresh_token
        }

        if scope:
            params['scope'] = scope

        logger.debug("Sending command `get_access_token_by_refresh_token` with"
                     " params %s", params)
        response = self.msgr.request("get_access_token_by_refresh_token",
                                     **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])
        return response['data']

    def get_user_info(self, access_token):
        """Function to get the information about the user using the access code
        obtained from the OP

        Note:
            Refer to the /.well-known/openid-configuration URL of your OP for
            the complete list of the claims for different scopes.

        Args:
            access_token (string): access token from the get_tokens_by_code
                                    function

        Returns:
            dict: The user data claims that are returned by the OP in format

            Example response::

                {
                    "sub": ["248289761001"],
                    "name": ["Jane Doe"],
                    "given_name": ["Jane"],
                    "family_name": ["Doe"],
                    "preferred_username": ["j.doe"],
                    "email": ["janedoe@example.com"],
                    "picture": ["http://example.com/janedoe/me.jpg"]
                }

        Raises:
            OxdServerError: If the param access_token is empty OR if the oxD
                Server returns an error.
        """
        params = dict(oxd_id=self.oxd_id, access_token=access_token)
        params["access_token"] = access_token
        logger.debug("Sending command `get_user_info` with params %s",
                     params)
        response = self.msgr.request("get_user_info", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])
        return response['data']['claims']

    def get_logout_uri(self, id_token_hint=None, post_logout_redirect_uri=None,
                       state=None, session_state=None):
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
        params = {"oxd_id": self.oxd_id}
        if id_token_hint:
            params["id_token_hint"] = id_token_hint

        if post_logout_redirect_uri:
            params["post_logout_redirect_uri"] = post_logout_redirect_uri

        if state:
            params["state"] = state

        if session_state:
            params["session_state"] = session_state

        logger.debug("Sending command `get_logout_uri` with params %s", params)
        response = self.msgr.request("get_logout_uri", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])
        return response['data']['uri']

    def update_site_registration(self):
        """Function to update the site's information with OpenID Provider.
        This should be called after changing the values in the cfg file.

        Returns:
            bool: The status for update. True for success and False for failure

        Raises:
            OxdServerError: When the update fails and oxd server returns error
        """
        params = {"oxd_id": self.oxd_id,
                  "authorization_redirect_uri": self.authorization_redirect_uri
                  }
        for param in self.opt_params:
            if self.config.get("client", param):
                value = self.config.get("client", param)
                params[param] = value

        for param in self.opt_list_params:
            if self.config.get("client", param):
                value = self.config.get("client", param).split(",")
                params[param] = value

        logger.debug("Sending `update_site_registration` with params %s",
                     params)
        response = self.msgr.request("update_site_registration", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])

        return True

    def uma_rs_protect(self, resources):
        """Function to be used in a UMA Resource Server to protect resources.

        Args:
            resources (list): list of resource to protect. See example at
                <https://gluu.org/docs/oxd/3.1.1/api/#uma-rs-protect-resources>_

        Returns:
            bool: The status of the request.
        """
        params = dict(oxd_id=self.oxd_id, resources=resources)

        logger.debug("Sending `uma_rs_protect` with params %s", params)
        response = self.msgr.request("uma_rs_protect", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])
        return True

    def uma_rs_check_access(self, rpt, path, http_method):
        """Function to be used in a UMA Resource Server to check access.

        Args:
            rpt (string): RPT or blank value if absent (not send by RP)
            path (string): Path of resource (e.g. for http://rs.com/phones,
                /phones should be passed)
            http_method (string) - Http method of RP request (GET, POST, PUT,
                DELETE)

        Returns:
            dict: The access information received in the format below.
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
        params = {"oxd_id": self.oxd_id,
                  "rpt": rpt,
                  "path": path,
                  "http_method": http_method}

        logger.debug("Sending command `uma_rs_check_access` with params %s",
                     params)
        response = self.msgr.request("uma_rs_check_access", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])
        return response['data']

    def uma_rp_get_rpt(self, ticket, claim_token=None, claim_token_format=None,
                       pct=None, rpt=None, scope=None, state=None):
        """Function to be used by a UMA Requesting Party to get RPT token.

        Args:
            ticket (str, REQUIRED): ticket
            claim_token (str, OPTIONAL): claim token
            claim_token_format (str, OPTIONAL): claim token format
            pct (str, OPTIONAL): pct
            rpt (str, OPTIONAL): rpt
            scope (list, OPTIONAL): scope
            state (str, OPTIONAL): state that is returned from
                `uma_rp_get_claims_gathering_url` command

        Returns:
            dict: The response from the OP

            Success Response::

                {
                    "status":"ok",
                    "data":{
                        "access_token":"SSJHBSUSSJHVhjsgvhsgvshgsv",
                        "token_type":"Bearer",
                        "pct":"c2F2ZWRjb25zZW50",
                        "upgraded":true
                    }
                }

        Raises:
            OxdServerError: When oxd-server reports a generic internal_error
            InvalidTicketError: When the oxd server returns a "invalid_ticket"
                error
            NeedInfoError: When the oxd server returns the "need_info" error.
                The details of the error can be obtained from the exception as
                a dict as shown below::

                    try:
                        rpt = client.uma_rp_get_rpt('ticket')
                    except NeedInfoError as e:
                        details = e.details

                The details dict::

                    {
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

        """
        params = {
            "oxd_id": self.oxd_id,
            "ticket": ticket
            }
        if claim_token:
            params["claim_token"] = claim_token
        if claim_token_format:
            params["claim_token_format"] = claim_token_format
        if pct:
            params["pct"] = pct
        if rpt:
            params["rpt"] = rpt
        if scope:
            params["scope"] = scope
        if state:
            params["state"] = state

        logger.debug("Sending command `uma_rp_get_rpt` with params %s", params)
        response = self.msgr.request("uma_rp_get_rpt", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'ok':
            return response['data']

        if response['data']['error'] == 'internal_error':
            raise OxdServerError(response['data'])

        if response['data']['error'] == 'need_info':
            raise NeedInfoError(response['data'])

        if response['data']['error'] == 'invalid_ticket':
            raise InvalidTicketError(response['data'])

    def uma_rp_get_claims_gathering_url(self, ticket):
        """UMA RP function to get the claims gathering URL.

        Args:
            ticket (str): ticket to pass to the auth server. for 90% of the
                cases, this will be obtained from 'need_info' error of get_rpt

        Returns:
            string specifying the claims gathering url
        """
        params = {
            'oxd_id': self.oxd_id,
            'claims_redirect_uri': self.config.get('client',
                                                   'claims_redirect_uri'),
            'ticket': ticket
        }
        logger.debug("Sending command `uma_rp_get_claims_gathering_url` with "
                     "params %s", params)
        response = self.msgr.request("uma_rp_get_claims_gathering_url", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])
        return response['data']['url']

    def setup_client(self):
        """The command registers the client for communication protection. This
        will be used to obtain an access token via the Get Client Token
        command. The access token will be passed as a protection_access_token
        parameter to other commands.

        Note:
            If you are using the oxd-https-extension, you must setup the client

        Returns:
            dict: the client setup information

            Example response::

                {
                    "oxd_id":"6F9619FF-8B86-D011-B42D-00CF4FC964FF",
                    "op_host": "<op host>",
                    "client_id":"<client id>",
                    "client_secret":"<client secret>",
                    "client_registration_access_token":"<Client registration access token>",
                    "client_registration_client_uri":"<URI of client registration>",
                    "client_id_issued_at":"<client_id issued at>",
                    "client_secret_expires_at":"<client_secret expires at>"
                }

        """
        # add required params for the command
        params = {
            "authorization_redirect_uri": self.authorization_redirect_uri,
            }

        # add other optional params if they exist in config
        for op in self.opt_params:
            if self.config.get("client", op):
                params[op] = self.config.get("client", op)

        for olp in self.opt_list_params:
            if self.config.get("client", olp):
                params[olp] = self.config.get("client", olp).split(",")

        logger.debug("Sending command `setup_client` with params %s", params)

        response = self.msgr.request("setup_client", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])
        data = response["data"]
        self.config.set("oxd", "id", data["oxd_id"])
        self.config.set("client", "client_id", data["client_id"])
        self.config.set("client", "client_secret", data["client_secret"])
        if data["client_registration_access_token"]:
            self.config.set("client", "client_registration_access_token",
                            data["client_registration_access_token"])
        if data["client_registration_client_uri"]:
            self.config.set("client", "client_registration_client_uri",
                            data["client_registration_client_uri"])
        self.config.set("client", "client_id_issued_at",
                        str(data["client_id_issued_at"]))

        return data


    def get_client_token(self, client_id=None, client_secret=None,
                         op_host=None, op_discovery_path=None, scope=None):
        """Function to get the client token which can be used for protection in
        all future communication. The access_token is stored in the config file
        and used for all future communication by oxdpython.

        Args:
            client_id (str, optional): client id from OP or from previous
                `setup_client` call
            client_secret (str, optional): client secret from the OP or from
                `setup_client` call
            op_host (str, optional): OP Host URL, default is read from the site
                configuration file
            op_discovery_path (str, optional): op discovery path provided by OP
            scope (list, optional): scopes of access required, default values
                are obtained from the config file

        Returns:
            dict: The client token and the refresh token in the form.

            Example response ::

                {
                    "access_token":"6F9619FF-8B86-D011-B42D-00CF4FC964FF",
                    "expires_in": 399,
                    "refresh_token": "fr459f",
                    "scope": "openid"
                }

        """
        # override the values from config
        params = dict(client_id=client_id, client_secret=client_secret,
                      op_host=op_host)

        if op_discovery_path:
            params['op_discovery_path'] = op_discovery_path
        if scope and isinstance(scope, list):
            params['scope'] = scope

        # If client id and secret aren't passed, then just read from the config
        if not client_id:
            params["client_id"] = self.config.get("client", "client_id")
        if not client_secret:
            params["client_secret"] = self.config.get("client",
                                                      "client_secret")
        if not op_host:
            params["op_host"] = self.config.get("client", "op_host")
        logger.debug("Sending command `get_client_token` with params %s",
                     params)

        response = self.msgr.request("get_client_token", **params)
        logger.debug("Received response: %s", response)

        if response['status'] == 'error':
            raise OxdServerError(response['data'])

        self.config.set("client", "protection_access_token",
                        response["data"]["access_token"])
        self.msgr.access_token = response["data"]["access_token"]
        return response['data']
