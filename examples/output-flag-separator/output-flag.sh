#!/bin/sh

set -u
set -e

function die {
  echo $*
  return 1 # terminates the script when the error flag is set
}

if [ $# != 2 ]
then
    echo $0 "<input> -o=<output_file>"
    exit 1
fi 

inputFile=$1
outputArg=$2

test -f ${inputFile} || die "Cannot find file ${inputFile}!"

[[ ${outputArg} == -o=* ]] || die "Output flag or file separator is incorrect"

outputFile=`echo ${outputArg} | awk -F '-o=' '{print $2}'`
cat ${inputFile} > ${outputFile}



