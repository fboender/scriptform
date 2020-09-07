#!/bin/sh


MYSQL_DEFAULTS_FILE="my.cnf"
MYSQL="mysql --defaults-file=$MYSQL_DEFAULTS_FILE"

echo "This is what would be executed if this wasn't a fake script:"
echo 
echo "    echo 'DROP DATABASE $target_db' | $MYSQL"
echo "    $MYSQL ${target_db} < ${sql_file}"

echo
echo "The uploaded file was $(stat --printf="%s" $sql_file) bytes"
echo "The (binary) md5 hash of the uploaded file is: $(md5sum -b $sql_file  | cut -d " " -f1)"
