#!/bin/sh

MYSQL_DEFAULTS_FILE="my.cnf"
MYSQL="mysql --defaults-file=$MYSQL_DEFAULTS_FILE"

echo "echo 'DROP DATABASE scriptform_acc' | $MYSQL"
echo "$MYSQL < dbs/${sample_db}.sql"
