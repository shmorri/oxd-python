class OxdServerError(Exception):
    """Error raises by oxdpython whenever a Oxd Server Error is reported
    """
    def __init__(self, data):
        error_string = "oxd Server Error: {0}\n {1}".format(
            data['error'], data['error_description'])
        Exception.__init__(self, error_string)


class InvalidTicketError(Exception):
    """Error raised when oxd-server returns a "invalid_ticket" error for the
    `uma_rp_get_rpt` command.
    """
    def __init__(self, data):
        error_string = "Invalid Ticket Error: {0}".format(
            data['error_description'])
        Exception.__init__(self, error_string)


class NeedInfoError(Exception):
    """Error raised when oxd-server returns a "need_info" error for the
    `uma_rp_get_rpt` command.
    """
    def __init__(self, data):
        error_string = "Need Info Error: {0}".format(
            data['error_description'])
        Exception.__init__(self, error_string)
        self.details = data['details']

class InvalidRequestError(Exception):
    """Error raised when UMA RP does an `uma_rp_check_access` on unprotected resource
    and the oxd server returns 'invalid_request' response.
    """
    def __init__(self, data):
        error_string = "Invalid Request Error: {0}".format(
            data['error_description']
        )
        Exception.__init__(self, error_string)
