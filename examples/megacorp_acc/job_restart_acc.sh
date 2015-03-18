#!/bin/sh

if [ "$passwd" != "123foobar" ]; then
    echo "Invalid password" >&2
    exit 1
fi

echo "RESTARTING"
ls -l /home/fboender
