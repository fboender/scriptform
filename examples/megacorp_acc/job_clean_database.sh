#!/bin/sh

if [ "$source_sql" = "empty" ]; then
    echo "Loading empty database"
    rm megacorp.db
    sqlite3 megacorp.db < megacorp_empty.sql && echo "Succesfully loaded"
else
    echo "Not Implemented"
fi
