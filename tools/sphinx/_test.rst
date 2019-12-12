Python API
==========
usage: Perform all the tests defined within the given descriptor
       [-h] descriptor

positional arguments:
  descriptor  The Boutiques descriptor as a JSON file, JSON string or Zenodo
              ID (prefixed by 'zenodo.').

optional arguments:
  -h, --help  show this help message and exit


**test**
========

.. argparse::
    :module: bosh
    :func: parser_test
    :prog: bosh test
