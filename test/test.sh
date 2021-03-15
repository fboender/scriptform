#!/bin/sh

#
# Script that's called by formconfig to test things. This is not the main
# script to run tests. For that, see the "build.sla" file in the root dir of
# this project.
#

cat << EOF
HTTP/1.0 200 Ok
echo "Content-type: text/plain"

EOF
env
