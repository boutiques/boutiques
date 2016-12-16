#!/bin/sh

set -u
set -e

function die {
  echo $*
  return 1 # terminates the script when the error flag is set
}

if [ $# != 2 ]
then
    echo $0 "<param> <outputFile>"
    echo "Param must be one of \"a\", \"b\" or \"c\"."
    exit 1
fi 

inputParam=$1
outputFile=$2

[[ ${inputParam} == "a" ]] || [[ ${inputParam} == "b" ]] || [[ ${inputParam} == "c" ]] || die "Incorrect param: ${inputParam}"

echo ${inputParam} > ${outputFile}



