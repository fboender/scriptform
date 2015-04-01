#!/bin/sh

cat << EOF
HTTP/1.0 200 Ok
Content-Type: image/jpeg

EOF
cat test.jpg
