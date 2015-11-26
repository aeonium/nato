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

import os
from pkg_resources import resource_string
from urlparse import urljoin

JUPYTER_SERVER_PATH = '/etc/nginx/jupyter-servers'


class ReverseProxyManager:
    def __init__(self, url_base):
        self.url_base = url_base

    def add_node(self, node):
        tpl = resource_string('nato.managers', 'jupyter-server.tpl')
        with open(os.path.join(JUPYTER_SERVER_PATH, node['uuid']), 'w') as f:
            subs = {'SERVER_ID': node['uuid'], 'SERVER_IP': node['ip']}
            f.write(tpl % subs)
            f.close()
        server_file = os.path.join(JUPYTER_SERVER_PATH, node['uuid'])
        return {'http': urljoin(self.url_base, node['uuid'])}

    def remove_node(self, mapping):
        server_file = os.path.join(JUPYTER_SERVER_PATH, mapping['uuid'])
        if os.path.exists(server_file):
            os.remove(os.path.join(JUPYTER_SERVER_PATH, mapping['uuid']))
