# Boutiques Tools
Tools to create and use boutiques descriptors.

Note: there is a Docker image ([boutiques/boutiques](https://hub.docker.com/r/boutiques/boutiques)) with the tools installed.

1. `validator.rb`: a Ruby script to validate Boutiques descriptors. Requires Ruby >= 2.0.
  * Installation:
    * `gem install bundler`
    * `bundle install`
  * Usage:
    * `validator.rb ../schema/descriptor.schema.json ./tool.json`
  * Usage example with Docker image:
    * `docker run --rm -v $PWD:/work -w /work boutiques/boutiques validator.rb /usr/local/boutiques/schema/descriptor.schema.json ./tool.json`

2. `localExec.py`: a Python script to test inputs on Boutiques JSON descriptors.
  * Usage examples:
    * Generates 4 random command lines: `docker run --rm -v $PWD:/work -w /work boutiques/boutiques localExec.py -n 4 -r ./tool.json`
    * Execute with an input file of parameters: `docker run --rm -v $PWD:/work -w /work boutiques/boutiques localExec.py -i input_param_file.json -e ./tool.json`
    * Print a command line based on parameters from an input file: `docker run --rm -v $PWD:/work -w /work boutiques/boutiques localExec.py -i input_param_file.csv ./tool.json`
  * Check the help page (`-h` option) for more options and documentation.

3. `invocationSchemaHandler.py`: a Python script to generate and test invocation schemas (i.e. JSON schemas for input values) associated to a Boutiques application
     descriptor and validating input data examples with respect to these invocation schemas.
  * Usage examples:
    * Generates an invocation schema: `docker run --rm -v $PWD:/work -w /work boutiques/boutiques  invocationSchemaHandler.py -i ./toolDescriptor.json`
    * Validate input data (i.e. specific tool parameter arguments): `docker run --rm -v $PWD:/work -w /work boutiques/boutiques invocationSchemaHandler.py -i ./toolDescriptor.json -d ./tool.exampleInputs.json`
  * Check the help page (`-h` option) for more options and documentation.

4. `pegasus-boutiques`: a python API to generate [Pegasus](https://pegasus.isi.edu) workflows from Boutiques JSON descriptors.

