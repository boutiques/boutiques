#!/bin/bash
cd tools/python/

cleanAndSetup(){
    yes | ./cleanup_tests.sh
    echo "" > stdout.txt
    chmod 777 stdout.txt
}&> /dev/null

runTestsForEnv(){
    cleanAndSetup
    echo "Testing for py$1"
    source env/boutiques_py$1/bin/activate
    pytest -q --disable-pytest-warnings
    deactivate
}

runTestsForEnv 2.7
runTestsForEnv 3.6
runTestsForEnv 3.7
cleanAndSetup
rm stdout.txt 
