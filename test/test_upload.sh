#!/bin/sh

MD5_UPLOAD=$(md5sum ${file} | cut -d" " -f1)
MD5_ORIG=$(md5sum "data.raw" | cut -d" " -f1)

if [ "$MD5_UPLOAD" = "$MD5_ORIG" ]; then
    echo "SAME"
else
    echo "DIFFERENT"
fi
