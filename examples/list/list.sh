#!/bin/sh

set -u
set -e

if [ $# -lt 2 ]
then
    echo $0 "<output_file> <input_files>"
    exit 1
fi 

outputFile=$1
shift

\rm ${outputFile}

while [ $# != 0 ]
do
  inputFile=$1
  test -f ${inputFile} || echo "Cannot find file ${inputFile}!"
  cat ${inputFile} >> ${outputFile}
  shift
done



