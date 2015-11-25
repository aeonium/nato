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

from .watcher import NatoWatcher
from .managers import PortManager, ReverseProxyManager

ETCD_HOST = str(os.getenv('ETCD_HOST', None))
ETCD_PORT = int(os.getenv('ETCD_PORT', None))
EXTERNAL_IP = str(os.getenv('EXTERNAL_IP', None))


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
