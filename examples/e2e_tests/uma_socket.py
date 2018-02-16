import os
import traceback
import logging
import argparse
import urlparse

from oxdpython import Client
from oxdpython.utils import ResourceSet

def run_commands(config):
    """function that runs the commands for UMA RS app context

    :param config: config file location
    :return: None
    """
    c = Client(config)

    print "\n=> Registering client using register_site()"
    oxd_id = c.register_site()
    logging.info("Received: %s", oxd_id)

    print "\n=> Protecting Resource: "
    rset = ResourceSet()
    r = rset.add("/photoz")
    r.set_scope("GET", "https://photoz.example.com/uma/scope/view")
    print rset
    protected = c.uma_rs_protect(rset.dump())
    logging.info("Received: %s", protected)

    print "\n=> Checking Access for URL /photoz, with method GET"
    access_status = c.uma_rs_check_access(rpt=None, path='/photoz', http_method='GET')
    print "\n=> Checking Access Response:", access_status
    logging.info('Received: %s', access_status)

    print "\n=> Get RPT (Need Info Error)"
    need_info = c.uma_rp_get_rpt(ticket=access_status['ticket'])
    logging.info('Received: %s', need_info)

    print "\n=> Get Claims Gathering Url"
    claims_url = c.uma_rp_get_claims_gathering_url(ticket=need_info['details']['ticket'])
    print "Visit this URL in your browser: ", claims_url
    logging.info('Received: %s', claims_url)

    print "\n=> Get RPT"
    callback_url = raw_input("Enter redirected URL to parse ticket and state: ")
    parsed = urlparse.urlparse(callback_url)
    params = urlparse.parse_qs(parsed.query)
    rpt_resp = c.uma_rp_get_rpt(ticket=params['ticket'][0], state=params['state'][0])
    logging.info("Received: %s", rpt_resp)

    print "\n=> Introspect RPT"
    introspection = c.introspect_rpt(rpt=rpt_resp['access_token'])
    logging.info('Received: %s', introspection)

    print "\n=> Checking Access for URL /photoz, with RPT and method GET"
    access = c.uma_rs_check_access(rpt=rpt_resp['access_token'], path='/photoz', http_method='GET')
    print "\n=> Checking Access Response:", access
    logging.info('Received: %s', access)


    print "\n=> Protecting Resource with Scope_expression"
    rset = ResourceSet()
    r = rset.add("/photo")
    scope_expr = {
        "rule": {
            "and": [{
                "or": [{
                    "var": 0
                },
                    {
                        "var": 1
                    }
                ]
            },
                {
                    "var": 2
                }
            ]
        },
        "data": [
            "http://photoz.example.com/dev/actions/all",
            "http://photoz.example.com/dev/actions/add",
            "http://photoz.example.com/dev/actions/internalClient"
        ]
    }
    r.set_expression("GET", scope_expr)
    print rset
    protected = c.uma_rs_protect(rset.dump())
    logging.info("Received: %s", protected)

    print "\n=> Checking Access for URL /photo, with scope_expression"
    access_status = c.uma_rs_check_access(rpt=None, path='/photo', http_method='GET')
    print "\n=> Checking Access Response:", access_status
    logging.info('Received: %s', access_status)


if __name__ == '__main__':
    this_dir = os.path.dirname(os.path.realpath(__file__))
    config = os.path.join(this_dir, 'uma_socket.cfg')
    test_config = os.path.join(this_dir, 'test.cfg')
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    config = os.path.join(this_dir, 'uma_socket.cfg')
    test_config = os.path.join(this_dir, 'test.cfg')


    with open(test_config, 'w') as of:
        with open(config) as f:
            of.write(f.read())

    try:
        run_commands(test_config)
    except:
        print traceback.print_exc()

    os.remove(test_config)


