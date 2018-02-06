import json, tempfile

def pytest_addoption(parser):
    parser.addoption("--descriptor", action="append", default=[],
        help="list of stringinputs to pass to test functions")


def fetchTests(descriptorFileName):
	descriptor = json.loads(open(descriptorFileName).read());
	tests = [];
	print(descriptor);
	
	# For each test present in the descriptor:
	for test in descriptor["tests"]:

		# Invocations may not have specified. In such case, we simply skip the current test.
		if (not test.has_key("invocation")):
			continue	

		# We first extract the invocation and put it inside a temporary file.
		invocationJSON = json.dumps(test["invocation"])
		tempInvocationJSON = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
		tempInvocationJSON.write(invocationJSON)
		tempInvocationJSON.seek(0)
		
		# Now we setup the necessary elements for the testing function.
		# Those elements are the descriptor itself + the test chunck from the descriptor + the invocation JSON temporary file.
		tests.append([descriptorFileName, test, tempInvocationJSON]);
		
		print("test added");
	return tests;
	


def pytest_generate_tests(metafunc):
	descriptorFileName =  metafunc.config.getoption('descriptor')
	print(descriptorFileName[0]);
	tests = fetchTests(descriptorFileName[0]);

	metafunc.parametrize("descriptor, test, invocation", tests)
