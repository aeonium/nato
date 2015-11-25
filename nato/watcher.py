#!/usr/bin/env python

import logging
import os

import etcd


LOG = logging.getLogger(__name__)


import subprocess
import ast
import io, sys

# Hardcoded config
nodes_key = '/nodes'
mappings_key = '/mappings'
locks_key = '/locks'
SSH_HOST_PATH='/ssh_hosts'

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
            nodes = _nodes_to_servers(self.client.read(nodes_key,
                                                       recursive=True))
        except etcd.EtcdKeyNotFound:
            pass
        return nodes

    def _get_mappings(self):
        nodes = {}
        try:
            nodes = _mappings_to_servers(self.client.read(mappings_key,
                                                          recursive=True))
        except etcd.EtcdKeyNotFound:
            pass
        return nodes

    def remove_mapping(self, uuid, mapping):
        try:
            self.client.read(mappings_key + '/' + uuid)
        except etcd.EtcdKeyNotFound:
            return
            pass
        # XXX TODO move this to a with thinggy
        try:
            # 60 seconds TTL should be enough for anyone to get this done
            self.client.write(locks_key + '/' + uuid, 'lock', ttl=60, prevExist=False)
        except etcd.EtcdAlreadyExist:
            # do not mess with locked uuid
            return
        try:
            LOG.info("[MAP] %s", mapping)
            for m in self.managers:
                m.remove_node(mapping)
                LOG.info("[OFFLINE] %s" % uuid)
            self.client.delete(mappings_key + '/' + uuid, recursive=True)
            self.client.delete(locks_key + '/' + uuid)
        except etcd.EtcdKeyNotFound:
            pass

    def add_mapping(self, uuid, node):
        LOG.debug("Trying to add new mapping to server %s" % uuid)
        try:
            self.client.read(mappings_key + '/' + uuid)
            # someone did the mapping already, go away
            LOG.info("Existing mapping, nothing to do")
            return
        except etcd.EtcdKeyNotFound:
            pass
        try:
            # 60 seconds TTL should be enough to get this done
            self.client.write(locks_key + '/' + uuid, 'lock', ttl=60, prevExist=False)
            base_key = '/'.join([mappings_key, uuid])
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
            self.client.delete(locks_key + '/' + uuid)


    def watch(self):
        self.client = etcd.Client(host=self.host, port=self.port,
                                  allow_reconnect=True)
        
        filelist = [ f for f in os.listdir(SSH_HOST_PATH)]
        for f in filelist:
            os.remove(os.path.join(SSH_HOST_PATH,f))

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
                self.client.read(nodes_key, recursive=True, wait=True)
            except etcd.EtcdException:
                # we cannot distinguish a timeout from anything else so just
                # fail if we need to in the read above
                pass
