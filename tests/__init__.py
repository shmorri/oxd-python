import os

from oxdpython import Client


def teardown_package():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    configs = [os.path.join(this_dir, 'data', 'initial.cfg'),
               os.path.join(this_dir, 'data', 'umaclient.cfg')
               ]
    for config in configs:
        c = Client(config)
        c.config.set('oxd', 'id', '')
