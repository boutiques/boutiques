#!/bin/bash
# Legacy script: used to clean files generated during tests
# Now cleans temp-* files and dangling files from failed tests

rm -r temp-*.sh log*.txt config*.txt user-image.simg example.conf stdout.txt