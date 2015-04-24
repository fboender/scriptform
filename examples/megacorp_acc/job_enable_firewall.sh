#!/bin/sh

# FIXME: Validate ip address

if [ "$network" = "intra" ]; then
    NETWORK="192.168.1.0/24"
elif [ "$network" = "machine" ]; then
    NETWORK="192.168.1.12"
else
    echo "Invalid network >&2"
    exit 1
fi

echo "iptables -A INPUT -p tcp --source $ip_address --dest $NETWORK -j ACCEPT"
echo "echo \"iptables -A INPUT -p tcp --source $ip_address --dest $NETWORK -j ACCEPT\" | at now + $expire_days days"
