#!/bin/bash

#
# WARNING: Do not use if you have made changes to the `good.json` descriptor
# and have not yet committed them!
#

rm -r temp-*.sh log*.txt config*.txt .pytest_cache/
git checkout boutiques/schema/examples/good.json
git checkout boutiques/schema/examples/example1/example1.json
git checkout boutiques/schema/examples/tests_good.json
git checkout boutiques/schema/examples/tests_failure_reference.json
git checkout boutiques/schema/examples/tests_failure_output_id.json
git checkout boutiques/schema/examples/tests_failure_exitcode.json
