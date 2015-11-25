#!/usr/bin/env python

import os
from pkg_resources import resource_string
import subprocess
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
        #subprocess.call('service nginx reload', shell=True)
        return {'http': urljoin(self.url_base, node['uuid'])}

    def remove_node(self, mapping):
        server_file = os.path.join(JUPYTER_SERVER_PATH, mapping['uuid'])
        if os.path.exists(server_file):
            os.remove(os.path.join(JUPYTER_SERVER_PATH, mapping['uuid']))
            #subprocess.call('service nginx reload', shell=True)
