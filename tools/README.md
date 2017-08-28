# Boutiques Tools
Tools to create and use boutiques descriptors.

## Installation

* pip install boutiques

## Usage

1. `validator.py`: a validator of Boutiques descriptors.
     
2. `localExec.py`: a Python script to test inputs on Boutiques JSON descriptors.
  * Usage examples:
    * Generates 4 random command lines: `localExec.py -n 4 -r ./tool.json`
    * Execute with an input file of parameters: `localExec.py -i input_param_file.json -e ./tool.json`
    * Print a command line based on parameters from an input file: `localExec.py -i input_param_file.csv ./tool.json`
  * Check the help page (`-h` option) for more options and documentation.

3. `invocationSchemaHandler.py`: a Python script to generate and test invocation schemas (i.e. JSON schemas for input values) associated to a Boutiques application
     descriptor and validating input data examples with respect to these invocation schemas.
  * Usage examples:
    * Generates an invocation schema: `invocationSchemaHandler.py -i ./toolDescriptor.json`
    * Validate input data (i.e. specific tool parameter arguments): `invocationSchemaHandler.py -i ./toolDescriptor.json -d ./tool.exampleInputs.json`
  * Check the help page (`-h` option) for more options and documentation.

4. `pegasus-boutiques`: a python API to generate [Pegasus](https://pegasus.isi.edu) workflows from Boutiques JSON descriptors.

## Contribution guidelines

* Fork the repo, commit and make pull requests to the `develop` branch.
* Use the [PEP8](https://www.python.org/dev/peps/pep-0008) style guide.