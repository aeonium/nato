#!/usr/bin/env python


import etcd
cli = etcd.Client()
cli.delete('/nodes', recursive=True)
cli.delete('/mappings', recursive=True)
cli.delete('/uports', recursive=True)
