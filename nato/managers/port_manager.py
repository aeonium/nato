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
import subprocess

import etcd

LOG = logging.getLogger(__name__)


# XXX FIXME HARCODED CONFIG!
UPORTS_KEY='/uports'
MIN_PORT=20000
MAX_PORT=25000
SSH_HOST_PATH='/ssh_hosts'

class PortManager:
    """Manages firewall."""
    def __init__(self, host, port, external_ip):
        self.client = etcd.Client(host=host, port=port,
                       allow_reconnect=True)
        self.external_ip = external_ip
        self._uports = []
        try:
            self._uports = ast.literal_eval(self.client.read(UPORTS_KEY).value)
        except:
            pass

    def str(self):
        return str(self._uports)

    def unused_port(self):
        if not self._uports:
            return MIN_PORT

        top = max(self._uports)
        unused = list(set(range(MIN_PORT, top)) - set(self._uports))
        if unused:
            return min(unused)
        if top != MAX_PORT:
            return top + 1;
        else:
            return None

    def append(self, port):
        self._uports.append(port)
        self.client.write(UPORTS_KEY, self._uports)

    def remove(self, port):
        try:
            self._uports.remove(port)
            self.client.write(UPORTS_KEY, self._uports)
        except ValueError:
            # XXX ay!
            pass

    def add_node(self, node):
        # XXX possible race condition?
        port = self.unused_port()
        self.append(port)
        d = {'port': port, 'node_ip': node['ip']}
        open(os.path.join(SSH_HOST_PATH, '%(node_ip)s_%(port)s' % d), 'w').close()        
        # FIXME: 22 hardcoded there
        #cmd = ('iptables -t nat -A PREROUTING -i eth0 -p tcp '
        #       '--dport %(port)s -j DNAT --to %(ip)s:22') % d
        # TODO: error handling
        #LOG.debug("Adding rule to firewall: %s" % cmd)
        #subprocess.call(cmd, shell=True)
        return {'port': port, 'node_ip': node['ip'], 'ip': self.external_ip}

    def remove_node(self, mapping):
        ssh_host_file = os.path.join(SSH_HOST_PATH, '%(node_ip)s_%(port)s' % mapping)
        if os.path.exists(ssh_host_file):
            os.remove(ssh_host_file)
        
        # FIXME: 22 hardcoded there
        #cmd = ('iptables -t nat -D PREROUTING -i eth0 -p tcp '
        #       '--dport %(port)s -j DNAT --to %(node_ip)s:22') % mapping
        # TODO: error handling
        #LOG.debug("Removing rule from firewall: %s" % cmd)
        #subprocess.call(cmd, shell=True)
        self.remove(int(mapping['port']))
