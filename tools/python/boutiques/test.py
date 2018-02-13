import os.path
from boutiques import bosh, localExec
from boutiques import __file__ as bfile
import hashlib
import pytest


def test(descriptor, test, invocation):    
    # Run pipeline.
    exit_code, stdout, stderr = bosh(["exec", "launch", descriptor, invocation.name])
    
    # Choose appropriate assertion scenario
    assertions = test["assertions"]
    if "exit-code" in assertions:
        assert (exit_code == assertions["exit-code"])
    
    if "output-files" in assertions:
    
        # Setting up a new LocalExecutor instance just for the sake of computing the list of output files path, coupled with their respective ids.
        executor = localExec.LocalExecutor(descriptor,
                                 {"forcePathType"      : True})
        outputted = executor.getOutputFiles(invocation.name)
        
        for output_file in assertions["output-files"]:
            
            file_path = outputted[output_file["id"]]
            assert os.path.exists(file_path)
            
            # Optionaly, a reference may have been specified
            if "reference" in output_file:
                
                reference_path = output_file["reference"]
                # Ensure that this property point to an existing file
                assert os.path.exists(reference_path)
                
                # MD5 checksum comparaison
                compute_md5 = lambda file_name: hashlib.md5(open(file_name,'rb').read()).hexdigest()
                actual = compute_md5(file_path)
                reference = compute_md5(reference_path)                
                assert actual == reference
