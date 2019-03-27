import os.path as op
from boutiques import __file__ as bfile
import boutiques as bosh
import hashlib
import pytest


def compute_md5(filename):
    with open(filename, 'rb') as fhandle:
        return hashlib.md5(open(filename, 'rb').read()).hexdigest()


def test(descriptor, test, invocation):
    # Run pipeline.
    ret = bosh.execute("launch",
                       descriptor,
                       invocation.name,
                       "--skip-data-collection")
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

            # Optionaly, an md5 reference may have been specified
            if "md5-reference" in output_file:

                # MD5 checksum comparaison
                output_md5 = compute_md5(file_path)
                reference_md5 = output_file["md5-reference"]
                assert output_md5 == reference_md5
