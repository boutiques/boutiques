#!/bin/bash

#
# WARNING: Do not use if you have made changes to the `good.json` descriptor
# and have not yet committed them!
#

rm -r temp-*.sh log*.txt config*.txt file.txt creator_output.json \
      test-created-argparse-descriptor.json test-created-argparse-inputs.json \
      .pytest_cache/ bar.dat baz.txt cwl_inv_out.json cwl_out.json \
      example.conf foo.txt goodbye.txt hello.js hello.tar stdout.txt \
      output-dir boutiques/tests/test-data-cache \
      TEST.one.three.two_out1.txt TEST_string1.txt test_temp
#git checkout boutiques/schema/examples/good.json
#git checkout boutiques/schema/examples/example1/example1_docker.json
#git checkout boutiques/schema/examples/example1/example1_sing.json
#git checkout boutiques/schema/examples/tests_good.json
#git checkout boutiques/schema/examples/tests_failure_reference.json
#git checkout boutiques/schema/examples/tests_failure_output_id.json
#git checkout boutiques/schema/examples/tests_failure_exitcode.json
