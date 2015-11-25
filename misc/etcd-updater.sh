#!/bin/sh
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
#
# This script will just send to the etcd a heads-up
# from the node. Should be added to a cron or similar
#

ETCD_URL="http://193.146.75.165:4001"
TTL="600"
ROOT="nodes"

# get id and IP from meta-data
ID=$(curl http://169.254.169.254/openstack/latest/meta_data.json | \
     python2 -c "import json; import sys; print json.load(sys.stdin)['uuid']")
IP=$(curl http://169.254.169.254/latest/meta-data/local-ipv4)

# XXX missing AuthN
curl -L $ETCD_URL/v2/keys/$ROOT/$ID -XPUT -d value=$IP -d ttl=$TTL &> /dev/null