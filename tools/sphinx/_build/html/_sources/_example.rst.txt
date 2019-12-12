Python API
==========
usage: Generates example invocation from a validdescriptor [-h] [-c]
                                                           descriptor

positional arguments:
  descriptor      The Boutiques descriptor as a JSON file, JSON string or
                  Zenodo ID (prefixed by 'zenodo.').

optional arguments:
  -h, --help      show this help message and exit
  -c, --complete  Include optional parameters.


**example**
===========

.. argparse::
    :module: bosh
    :func: parser_example
    :prog: bosh example
