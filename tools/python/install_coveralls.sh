#!/usr/bin/env bash

set -e
set -u

MAJOR_VER=$(python -c 'import sys; print(sys.version_info[0])')
MINOR_VER=$(python -c 'import sys; print(sys.version_info[1])')
if [ "${MINOR_VER}" == "6" ] && [ "${MAJOR_VER}" == "2" ]
then
    # Use older version of pyOpenSSL
    pip install pyOpenSSL==17.5.0
else
    # Use latest version
    pip install pyOpenSSL
fi
# Now coveralls will use the old version of pyOpenSSL when using Python 2.6
pip install coveralls
