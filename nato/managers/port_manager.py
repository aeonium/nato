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

import ast
import logging
import os

import etcd
from oslo_config import cfg

from nato import utils

LOG = logging.getLogger(__name__)

opts = [
    cfg.StrOpt('uports-key',
               default='/uports',
               help='Etcd key to store the used ports'),
    cfg.IntOpt('min-port',
               default=20000,
               help='First port of range to map'),
    cfg.IntOpt('max-port',
               default=25000,
               help='Last port of rang to map'),
    cfg.StrOpt('map-path',
               default=utils.env('NATO_MAP_PATH', '/ssh_hosts'),
               help='Path to store the files with the mappings'
                    'default env[NATO_MAP_PATH] or /ssh_hosts'),
]

CONF = cfg.CONF
CONF.register_opts(opts, group="portmanager")
CONF.register_cli_opts(opts, group="portmanager")


class PortManager:
    """Manages firewall."""
    def __init__(self, host, port, external_ip):
        # cleans up any previous mapping
        filelist = [f for f in os.listdir(CONF.map_path)]
        for f in filelist:
            os.remove(os.path.join(CONF.map_path,f))

        self.client = etcd.Client(host=host, port=port,
                       allow_reconnect=True)
        self.external_ip = external_ip
        self._uports = []
        try:
            self._uports = ast.literal_eval(
                self.client.read(CONF.uports_key).value)
        except:
            pass

    def str(self):
        return str(self._uports)

    def unused_port(self):
        if not self._uports:
            return CONF.min_port
        top = max(self._uports)
        unused = list(set(range(CONF.min_port, top)) - set(self._uports))
        if unused:
            return min(unused)
        if top != CONF.max_port:
            return top + 1;
        else:
            return None

    def append(self, port):
        self._uports.append(port)
        self.client.write(CONF.uports_key, self._uports)

    def remove(self, port):
        try:
            self._uports.remove(port)
            self.client.write(CONF.uports_key, self._uports)
        except ValueError:
            # XXX ay!
            pass

    def add_node(self, node):
        # XXX possible race condition?
        port = self.unused_port()
        self.append(port)
        d = {'port': port, 'node_ip': node['ip']}
        open(os.path.join(CONF.map_path,
                          '%(node_ip)s_%(port)s' % d), 'w').close()
        return {'port': port, 'node_ip': node['ip'], 'ip': self.external_ip}

    def remove_node(self, mapping):
        ssh_host_file = os.path.join(CONF.map_path,
                                     '%(node_ip)s_%(port)s' % mapping)
        if os.path.exists(ssh_host_file):
            os.remove(ssh_host_file)
        self.remove(int(mapping['port']))
