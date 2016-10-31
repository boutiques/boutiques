#!/bin/sh

set -u
set -e

if [ $# != 2 ]
then
    echo $0 "<input> <output_file>"
    exit 1
fi 

inputFile=$1
outputFile=$2

test -f ${inputFile} || echo "Cannot find file ${inputFile}!"

cat ${inputFile} > ${outputFile}



