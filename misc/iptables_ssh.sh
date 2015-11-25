#!/usr/bin/env bash

WAN_IFACE=eth0
MAP_DIR=/ssh_hosts

iptables -t nat -F SSH

for f in $MAP_DIR/*; do
    if [[ -f $f &&  "$f" != ^. ]]; then
        filename=${f##*/}    
        ip=${filename%_*}
        port=${filename##*_}
        iptables -t nat -A SSH -i $WAN_IFACE -p tcp --dport $port -j DNAT --to $ip:22
    fi
done

