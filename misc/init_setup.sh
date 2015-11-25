#!/usr/bin/env bash
echo "Enabling ip forwarding..."
WAN_IFACE=eth0
sysctl -w net.ipv4.ip_forward=1 

echo "Setting Rules in iptables..."
iptables -t nat -APOSTROUTING -d 172.16.27.0/24 -p tcp -m tcp --dport 22 -j MASQUERADE
iptables -t nat -F SSH
iptables -t nat -N SSH
iptables -t nat -A PREROUTING -j SSH

echo "Installing incron..."
apt-get update \
&& apt-get -qy upgrade --fix-missing --no-install-recommends \
&& apt-get -qy install --fix-missing --no-install-recommends \
    incron

echo root > /etc/incron.allow \
&& echo "/ssh_hosts IN_MODIFY,IN_CREATE,IN_DELETE /home/ubuntu/iptables_ssh.sh" | incrontab - \
&& /etc/init.d/incron start




