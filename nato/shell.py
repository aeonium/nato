# This file is part of Lifewatch DAAP.
# Copyright (C) 2015 Ana Yaiza Rodriguez Marrero.
#
# Lifewatch DAAP is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lifewatch DAAP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lifewatch DAAP. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import logging
import logging.config
import json
import os
import sys

from oslo_config import cfg

import nato
from nato.utils import env
from nato.watcher import NatoWatcher
from nato.managers import PortManager, ReverseProxyManager


opts = [
    cfg.StrOpt('logging_conf',
               default=env('LOG_CFG', 'logging.json'),
               help='Logging configuration file (default value env[LOG_CFG]'
                    'or logging.json)'),
    cfg.BoolOpt('debug',
                short='d',
                default=False,
                help='Print debug output (set logging level to '
                     'DEBUG instead of default WARNING level).'),
    cfg.StrOpt('external-ip',
               required=True,
               default=env('EXTERNAL_IP', None),
               help='External IP of the bridge machine'),
    cfg.StrOpt('etcd-host',
               required=True,
               default=env('ETCD_HOST', None),
               help='etcd host'),
    cfg.StrOpt('etcd-port',
               required=True,
               default=env('ETCD_PORT', None),
               help='etcd host'),
]

CONF = cfg.CONF
CONF.register_cli_opts(opts)
CONF.register_opts(opts)


def parse_args(argv, default_config_files=None):
    CONF(argv[1:],
         project='nato',
         version=nato.__version__,
         default_config_files=default_config_files)


def setup_logging(config_file, debug=False):
    """
    Setup logging configuration
    """
    log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG
    if os.path.exists(config_file):
        with open(config_file, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=log_level)


def main():
    parse_args(sys.argv)
    setup_logging(CONF.logging_conf, CONF.debug)
    LOG = logging.getLogger(__name__)
    LOG.info("NATO Starting")
    managers = [PortManager(CONF.etcd_host, CONF.etcd_port, CONF.external_ip),
                ReverseProxyManager('http://' + CONF.external_ip)]
    watcher = NatoWatcher(CONF.etcd_host, CONF.etcd_port, managers)
    watcher.watch()


if __name__ == '__main__':
    main()
