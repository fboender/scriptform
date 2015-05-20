#!/bin/sh

# This starts a child process in the background which will block since its file
# descriptors are still tied to us.
sleep 10000 &> /dev/null 

echo "some test error" >&2

cat /usr/share/dict/american-english

exit 1
