import os.path
from boutiques import bosh, execute
from boutiques import __file__ as bfile
import pytest


def test(descriptor, test, invocation):
	print("invocation: %s" % invocation.name);
	print("test: %s" % test["name"])

	exitCode = -1

	# Run pipeline.
	try:
		execute("launch", descriptor, invocation.name)
	except SystemExit as e:
		exitCode = e.code

	# Choose appropriate assertion scenario
	assertions = test["assertions"]
	if (assertions.has_key("exit-code")):
		assert (exitCode == assertions["exit-code"])
		
	if (assertions.has_key("output-files")):
		for outputFile in assertions["output-files"]:
			
			# We check the path (the path is garanteed to be here as it is required by the descriptor for an output-file)
			targetPath = outputFile["path"]
			assert os.path.isfile(targetPath) == True
		
			# Addtionaly, we might have included a reference.
			# In this case we need to compare the inside of the reference file with the content of the outputted file.
			referencePath = outputFile["reference"]
			# (We assume that the reference file exist) 
			referenceContent = open(referencePath, 'r').read()
			targetContent = open(targetPath, 'r').read()
			
			# Proceed to the content comparaison.
			assert referenceContent == targetContent
