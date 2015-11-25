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

import logging
import os
import sys

import etcd
from oslo_config import cfg

LOG = logging.getLogger(__name__)

opts = [
    cfg.StrOpt('nodes-key',
               default='/nodes',
               help='Etcd key to find nodes'),
    cfg.StrOpt('mappings-key',
               default='/mappings',
               help='Etcd key to define mappings'),
    cfg.StrOpt('locks-key',
               default='/locks',
               help='Etcd key to crreate locks'),
]

CONF = cfg.CONF
CONF.register_opts(opts, group="watcher")
CONF.register_cli_opts(opts, group="watcher")


def _nodes_to_servers(r):
    s = {}
    for child in r.children:
        keys = child.key.rsplit('/', 1)
        if not keys[0]:
            continue
        s[keys[-1]] = {'ip': child.value, 'uuid': keys[-1]}
    return s


def _mappings_to_servers(r):
    s = {}
    for child in r.children:
        keys = child.key.rsplit('/', 2)
        if not keys[0]:
            continue
        k, sub_k = keys[1], keys[2]
        v = s.get(k, {})
        v[sub_k] = child.value
        v['uuid'] = k
        s[k] = v
    return s


class NatoWatcher:
    def __init__(self, host, port, managers):
        self.host = host
        self.port = port
        self.managers = managers

    def _get_nodes(self):
        nodes = {}
        try:
            nodes = _nodes_to_servers(self.client.read(CONF.nodes_key,
                                                       recursive=True))
        except etcd.EtcdKeyNotFound:
            pass
        return nodes

    def _get_mappings(self):
        nodes = {}
        try:
            nodes = _mappings_to_servers(self.client.read(CONF.mappings_key,
                                                          recursive=True))
        except etcd.EtcdKeyNotFound:
            pass
        return nodes

    def remove_mapping(self, uuid, mapping):
        try:
            self.client.read(CONF.mappings_key + '/' + uuid)
        except etcd.EtcdKeyNotFound:
            return
            pass
        # XXX TODO move this to a with thinggy
        try:
            # 60 seconds TTL should be enough for anyone to get this done
            self.client.write(CONF.locks_key + '/' + uuid, 'lock', ttl=60,
                              prevExist=False)
        except etcd.EtcdAlreadyExist:
            # do not mess with locked uuid
            return
        try:
            LOG.info("[MAP] %s", mapping)
            for m in self.managers:
                m.remove_node(mapping)
                LOG.info("[OFFLINE] %s" % uuid)
            self.client.delete(CONF.mappings_key + '/' + uuid, recursive=True)
            self.client.delete(CONF.locks_key + '/' + uuid)
        except etcd.EtcdKeyNotFound:
            pass

    def add_mapping(self, uuid, node):
        LOG.debug("Trying to add new mapping to server %s" % uuid)
        try:
            self.client.read(CONF.mappings_key + '/' + uuid)
            # someone did the mapping already, go away
            LOG.info("Existing mapping, nothing to do")
            return
        except etcd.EtcdKeyNotFound:
            pass
        try:
            # 60 seconds TTL should be enough to get this done
            self.client.write(CONF.locks_key + '/' + uuid, 'lock', ttl=60,
                              prevExist=False)
            base_key = '/'.join([CONF.mappings_key, uuid])
            for m in self.managers:
                map_info = m.add_node(node)
                LOG.info("[ONLINE] %s %s" % (uuid, map_info))
                for k, v in map_info.items():
                    self.client.write('/'.join([base_key, k]), v)
        except etcd.EtcdAlreadyExist:
            # do not mess with locked uuid
            LOG.debug("Existing lock, do not mess")
            return
        else:
            self.client.delete(CONF.locks_key + '/' + uuid)


    def watch(self):
        self.client = etcd.Client(host=self.host, port=self.port,
                                  allow_reconnect=True)
        
        while True:
            try:
                mapped = self._get_mappings()
                nodes = self._get_nodes()
            except etcd.EtcdException, e:
                LOG.error(e)
                continue

            LOG.debug("MAPPED %s" % mapped)
            LOG.debug("NODES %s" % nodes)

            mapped_ids = set(mapped.keys())
            nodes_ids = set(nodes.keys())
            if mapped_ids != nodes_ids:
                for s in mapped_ids - nodes_ids:
                    self.remove_mapping(s, mapped[s])
                for s in nodes_ids - mapped_ids:
                    self.add_mapping(s, nodes[s])
            else:
                LOG.debug("no change")

            try:
                self.client.read(CONF.nodes_key, recursive=True, wait=True)
            except etcd.EtcdException:
                # we cannot distinguish a timeout from anything else so just
                # fail if we need to in the read above
                pass
