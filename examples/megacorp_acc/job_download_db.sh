#!/bin/sh

FILESIZE=$(stat -c "%s" megacorp.db)
cat << EOF
HTTP/1.0 200 Ok
Content-Type: application/octet-stream
Content-Disposition: attachment; filename=megacorp.db
Content-Length: $FILESIZE

EOF
cat megacorp.db
