import simplejson as json
import tempfile
import os.path as op
from boutiques.util.utils import loadJson


def pytest_addoption(parser):
    parser.addoption("--descriptor", action="append", default=[])

    # Additional options during bosh exec launch:
    parser.addoption("--imagepath", action="store")


def fetch_tests(descriptor_input, paramsDict):
    descriptor = loadJson(descriptor_input)

    tests = []

    # For each test present in the descriptor:
    for test in descriptor["tests"]:

        # We first extract the invocation and put it inside a temporary file.
        invocation_JSON = json.dumps(test["invocation"])
        temp_invocation_JSON = tempfile.NamedTemporaryFile(suffix=".json",
                                                           delete=False)
        temp_invocation_JSON.write(invocation_JSON.encode())
        temp_invocation_JSON.seek(0)

        # Now we setup the necessary elements for the testing function.
        tests.append([descriptor_input, test, temp_invocation_JSON, paramsDict])

    return (descriptor["name"], tests)


# This function will be executed by pytest before the actual testing
def pytest_generate_tests(metafunc):
    descriptor_filename = metafunc.config.getoption('descriptor')[0]
    additional_params = {"--skip-data-collection": None}

    if metafunc.config.option.imagepath is not None:
        additional_params['--imagepath'] = metafunc.config.option.imagepath
    # Each element in 'tests' will hold the necessary information
    # for a single test
    # Those information are:
    #     . The descriptor (common to all)
    #     . The related JSON data, describing the test
    #       (more convenient, no need to extract
    #        again from descriptor)
    #     . The invocation file needed for the test
    #     . Any additional options listed in conftest.pytest_addoption()
    descriptor_name, tests = fetch_tests(descriptor_filename, additional_params)

    # Generate the test ids for each of the test cases.
    # An id is created by concatenaning the name of the descriptor
    # with the name of the test case.
    names = ["{0}_{1}".format(op.basename(descriptor_filename),
             params[1]["name"].replace(' ', '-')) for params in tests]

    metafunc.parametrize("descriptor, test, invocation, paramsDict",
                         tests, ids=names)
