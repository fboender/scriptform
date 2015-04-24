#!/bin/sh

echo "<table>"
{
    echo ".mode html"
    echo "SELECT * FROM employee;"
} | sqlite3 megacorp.db || exit 1
echo "</table>"
