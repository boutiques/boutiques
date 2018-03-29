import os.path as op
from boutiques import bosh, localExec
from boutiques import __file__ as bfile
import hashlib
import pytest


def compute_md5(filename):
   with open(filename, 'rb') as fhandle:
      return hashlib.md5(open(filename,'rb').read()).hexdigest()


def test(descriptor, test, invocation):    
    # Run pipeline.
    stdout, stderr, exit_code, err_msg = bosh(["exec", "launch", descriptor, invocation.name])
    
    # Choose appropriate assertion scenario
    assertions = test["assertions"]
    if "exit-code" in assertions:
        assert exit_code == assertions["exit-code"]
    
    if "output-files" in assertions:
    
        # Acquiring a hash map of output ids mapping to output file paths.
        outputted = bosh(["evaluate", descriptor, invocation.name, "output-files/"])
        
        for output_file in assertions["output-files"]:
            
            file_path = outputted[output_file["id"]]
            assert op.exists(file_path)
            
            # Optionaly, a reference may have been specified
            if "reference" in output_file:
                
                reference_path = output_file["reference"]
                # Ensure that this property point to an existing file
                assert op.exists(reference_path)
                
                # MD5 checksum comparaison
                actual = compute_md5(file_path)
                reference = compute_md5(reference_path)                
                assert actual == reference
