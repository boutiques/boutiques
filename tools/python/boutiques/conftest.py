import json, tempfile

def pytest_addoption(parser):
    parser.addoption("--descriptor", action="append", default=[])

def fetch_tests(descriptor_filename):
    
    descriptor = json.loads(open(descriptor_filename).read());
    tests = [];
    
    # For each test present in the descriptor:
    for test in descriptor["tests"]:

        # We first extract the invocation and put it inside a temporary file.
        invocation_JSON = json.dumps(test["invocation"])
        temp_invocation_JSON = tempfile.NamedTemporaryFile(suffix=".json", 
                                                           delete=False)
        temp_invocation_JSON.write(invocation_JSON.encode())
        temp_invocation_JSON.seek(0)
		
        # Now we setup the necessary elements for the testing function.
        tests.append([descriptor_filename, test, temp_invocation_JSON]);
        
    return tests;

# This function will be executed by pytest before proceeding to the actual testing
def pytest_generate_tests(metafunc):
    descriptor_filename =  metafunc.config.getoption('descriptor')

    # Each element in the following list will hold the necessary informations for a single test
    # Those informations are:
    #                         . The descriptor (common to all)
    #                         . The related JSON data, describing the test 
    #                         (more convenient, no need to extract again from descriptor)
    #                         . The invocation file needed for the test
    tests = fetch_tests(descriptor_filename[0]);
    metafunc.parametrize("descriptor, test, invocation", tests)
