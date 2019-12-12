Python API
==========
usage: Evaluates parameter values for a descriptor and invocation
       [-h] descriptor invocation [query [query ...]]

positional arguments:
  descriptor  The Boutiques descriptor as a JSON file, JSON string or Zenodo
              ID (prefixed by 'zenodo.').
  invocation  Input JSON complying to invocation.
  query       The query to be performed. Simply request keys from the
              descriptor (i.e. output-files), and chain together queries (i.e.
              id=myfile or optional=false) slashes between them and commas
              connecting them. (i.e. output-files/optional=false,id=myfile).
              Perform multiple queries by separating them with a space.

optional arguments:
  -h, --help  show this help message and exit


**evaluate**
============

.. argparse::
    :module: bosh
    :func: parser_evaluate
    :prog: bosh evaluate
