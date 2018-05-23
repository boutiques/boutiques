#!/usr/bin/env bash

set -e
set -u

MAJOR_VER=$(python -c 'import sys; print(sys.version_info[0])')
MINOR_VER=$(python -c 'import sys; print(sys.version_info[1])')
if [ "${MINOR_VER}" == "6" ] && [ "${MAJOR_VER}" == "2" ]
then
    pip install coveralls==1.2.0
else
    pip install coveralls
fi
