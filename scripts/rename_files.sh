#!/bin/bash

find . -type f -name 'TURX*' | while read FILE ; do
    newfile="$(echo ${FILE} |sed -e 's/TURX/PEUT/')" ;
    mv "${FILE}" "${newfile}" ;
done
