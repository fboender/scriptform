#!/bin/sh

FILESIZE=$(expr 1024 \* 1000 \* 100)
cat << EOF
HTTP/1.0 200 Ok
Content-Type: application/octet-stream
Content-Disposition: attachment; filename=large_file.dat
Content-Length: $FILESIZE

EOF
dd if=/dev/urandom bs=1024 count=100000
