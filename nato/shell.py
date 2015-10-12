#!/usr/bin/env python

from __future__ import absolute_import

import logging
import logging.config
import json
import os

from .watcher import NatoWatcher
from .managers import PortManager, ReverseProxyManager

# XXX HARDCODED CONFIG
ETCD_HOST = '127.0.0.1'
ETCD_PORT = 4001
EXTERNAL_IP = '193.146.75.165'


def setup_logging(default_path='logging.json', default_level=logging.INFO,
                  env_key='LOG_CFG'):
    """
    Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def main():
    setup_logging()
    LOG = logging.getLogger(__name__)
    LOG.info("NATO Starting")
    managers = [PortManager(ETCD_HOST, ETCD_PORT, EXTERNAL_IP),
                ReverseProxyManager('http://' + EXTERNAL_IP)]
    watcher = NatoWatcher(ETCD_HOST, ETCD_PORT, managers)
    watcher.watch()

if __name__ == '__main__':
    main()
