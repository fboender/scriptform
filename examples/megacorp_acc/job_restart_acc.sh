#!/bin/sh

if [ "$passwd" != "123foobar" ]; then
    echo "Invalid password" >&2
    exit 1
fi

echo "RESTARTING"

if [ $no_db = "on" ]; then
    echo "NOT RESTARTING DATABASE"
fi

ls -l /home/fboender
