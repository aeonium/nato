#!/bin/sh
#
# This script will just send to the etcd a heads-up
# from the node. Should be added to a cron or similar
#
# PARAMS
# $1 -> etcd URL [mandatory]
# $2 -> TTL [optional, default 300]
# $3 -> root key where to register [optional, default nodes]

DEFAULT_TTL=300
DEFAULT_ROOT=nodes

die () {
   echo >&2 "$@"
   exit 1
}

[ "x$1" = "x" ] && die "Missing etcd URL"
ETCD_URL="$1"
shift

if [ "x$1" = "x" ] ; then
    TTL=$DEFAULT_TTL
else
    TTL=$1
    shift
fi

if [ "x$1" = "x" ] ; then
    ROOT=$DEFAULT_ROOT
else
    ROOT=$1
fi

# get id and IP from meta-data
#ID=$(curl http://169.254.169.254/openstack/latest/meta_data.json | \
#     python2 -c "import json; import sys; print json.load(sys.stdin)['uuid']")
ID="b6d6d700-8ddf-4243-9379-f87f215c8fa3"
ID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1)

# XXX missing AuthN
curl -L $ETCD_URL/v2/keys/$ROOT/$ID -XPUT -d value='10.10.10.10' -d ttl=$TTL 
