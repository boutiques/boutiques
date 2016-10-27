#!/bin/sh

set -u
set -e

function die {
  echo $*
  return 1
}

if [ $# != 1 ]
then
  die $0 "<config file>"
fi 

# A file with the following syntax should be passed

# Mandatory Inputs
#   numInput=a
#   listNumInput=a,b,c
#   stringInput=a
#   fileInput=a
#   fileOutput=/a/b

# Optional Input
#   optStringInput=a
# Comments start with #

configFile=$1

test -f ${configFile} || die "File ${configFile} not found!"

while read line; do
    if [[ ${line} == \#* ]] || [[ ${line} == "" ]]
    then
        continue
    fi
    name=`echo ${line} | awk -F '=' '{print $1}'`
    value=`echo ${line} | awk -F '=' '{print $2}'`
    case $name in
        numInput*)
            numInput=${value}
            ;;
        listNumInput*)
            listNumInput=${value}
            ;;
        stringInput*)
            stringInput=${value}
            ;;
        fileInput*)
            fileInput=${value}
            ;;
        fileOutput*)
            fileOutput=${value}
            ;;
        optStringInput*)
            optStringInput=${value}
            ;;
        *)
            die "Unrecognized line: \"${line}\""
            
    esac
done <${configFile}

test -f ${fileInput} || die "Input file ${fileInput} not found!"

echo "The test was successful. Here are the mandatory parameters: ${numInput}, \"${listNumInput}\", ${stringInput}, ${fileInput}, ${fileOutput}" > ${fileOutput}



