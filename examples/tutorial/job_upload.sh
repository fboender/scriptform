#!/bin/sh

if [ -z "$name" ]; then
    name="stranger"
fi
echo "Hello, $name!"

if [ -z "$upload" ]; then
    echo "Looks like you didn't upload a file!"
else
    FILE_SIZE=$(wc -c $upload | cut -d " " -f1)
    echo "The size in bytes of $upload__name is $FILE_SIZE"
fi

