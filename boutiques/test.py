import os.path as op
from boutiques import __file__ as bfile
import boutiques as bosh
import hashlib


def compute_md5(filename):
    with open(filename, 'rb') as fhandle:
        return hashlib.md5(open(filename, 'rb').read()).hexdigest()


def test(descriptor, test, invocation, paramsDict):
    arguments = ["launch", descriptor, invocation.name]

    # Add any additional params to arguments
    for flag, value in paramsDict.items():
        arguments.append(flag)
        if value is not None:
            arguments.append(value)

    print(arguments)
    # Run pipeline.
    ret = bosh.execute(*arguments)
    print(ret)

    # Choose appropriate assertion scenario
    assertions = test["assertions"]
    if "exit-code" in assertions:
        assert ret.exit_code == assertions["exit-code"]

    if "output-files" in assertions:

        # Acquiring a hash map of output ids mapping to output file paths.
        outputted = bosh.evaluate(descriptor, invocation.name, "output-files/")

        for output_file in assertions["output-files"]:

            file_path = outputted[output_file["id"]]
            assert op.exists(file_path)

            # Optionally, an md5 reference may have been specified
            if "md5-reference" in output_file:

                # MD5 checksum comparison
                output_md5 = compute_md5(file_path)
                reference_md5 = output_file["md5-reference"]
                assert output_md5 == reference_md5
