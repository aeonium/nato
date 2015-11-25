#!/usr/bin/env bash
echo "Enabling ip forwarding..."
sysctl -w net.ipv4.ip_forward=1

echo "Flushing iptables rules"
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

echo "Restarting Docker (recompose its rules)..." 
service docker restart
