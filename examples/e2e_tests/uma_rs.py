import os
import traceback
import logging
import argparse

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
    status = c.uma_rs_check_access(rpt=None, path='/photoz', http_method='GET')
    logging.info('Received: %s', status)

if __name__ == '__main__':
    this_dir = os.path.dirname(os.path.realpath(__file__))
    config = os.path.join(this_dir, 'uma_rs.cfg')
    test_config = os.path.join(this_dir, 'test.cfg')
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    config = os.path.join(this_dir, 'uma_rs.cfg')
    test_config = os.path.join(this_dir, 'test.cfg')


    with open(test_config, 'w') as of:
        with open(config) as f:
            of.write(f.read())

    try:
        run_commands(test_config)
    except:
        print traceback.print_exc()

    os.remove(test_config)


