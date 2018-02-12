import os.path
from boutiques import bosh
from boutiques import __file__ as bfile
import pytest


def test(descriptor, test, invocation):
    print("invocation: %s" % invocation.name);
    print("test: %s" % test["name"])
    
    # Run pipeline.
    exit_code, stdout, stderr = bosh("exec", "launch", descriptor, invocation.name)

    # Choose appropriate assertion scenario
    assertions = test["assertions"]
    if (assertions.has_key("exit-code")):
        assert (exit_code == assertions["exit-code"])
	    
    if (assertions.has_key("output-files")):
        for output_file in assertions["output-files"]:
        # We check the path (the path is garanteed to be here as it is required by the descriptor for an output-file)
            target_path = output_file["path"]
	    assert os.path.isfile(targetPath)
	    # Addtionaly, we might have included a reference.
	    # In this case we need to compare the inside of the reference file with the content of the outputted file.
	    reference_path = output_file["reference"]
	    # (We assume that the reference file exist)
            # Do comparison using md5
	    reference_content = open(referencePath, 'r').read()
	    target_content = open(targetPath, 'r').read()
	    # Proceed to the content comparaison.
	    assert referenceContent == targetContent
            
