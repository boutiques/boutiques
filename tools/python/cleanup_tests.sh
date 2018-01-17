#!/bin/bash

#
# WARNING: Do not use if you have made changes to the `good.json` descriptor
# and have not yet committed them!
#

rm temp-*.sh log-*.txt config*.txt
git checkout boutiques/schema/examples/good.json
git checkout boutiques/schema/examples/example1/example1.json
