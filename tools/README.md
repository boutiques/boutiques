# Boutiques Tools
 
bosh (BOutiques SHell) suite of tools to create and use boutiques descriptors.

## Installation

* `pip install boutiques`

## Usage

1. `bosh-validate`: validate Boutiques descriptors.
     
2. `bosh`: test and run Boutiques tools.
  * Usage examples:
    * Generates 4 random command lines: `bosh -n 4 -r ./tool.json`
    * Execute with an input file of parameters: `bosh -i input_param_file.json -e ./tool.json`
    * Print a command line based on parameters from an input file: `bosh -i input_param_file.csv ./tool.json`
  * Check the help page (`-h` option) for more options and documentation.

3. `bosh-invocation`: generate and test invocation schemas (i.e. JSON schemas for input values) associated to a Boutiques application
     descriptor and validating input data examples with respect to these invocation schemas.
  * Usage examples:
    * Generates an invocation schema: `bosh-invocation -i ./toolDescriptor.json`
    * Validate input data (i.e. specific tool parameter arguments): `bosh-invocation -i ./toolDescriptor.json -d ./tool.exampleInputs.json`
  * Check the help page (`-h` option) for more options and documentation.

4. `bosh-import`: import BIDS apps or legacy Boutiques descriptors to latest schema.

5. `bosh-publish`: publish Boutiques descriptors to [Neurolinks](https://brainhack101.github.io/neurolinks).

6. `pegasus-boutiques`: a python API to generate [Pegasus](https://pegasus.isi.edu) workflows from Boutiques JSON descriptors.

