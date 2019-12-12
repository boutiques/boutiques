Python API
==========
usage: Creates invocation schema and validates invocations. Uses descriptor's invocation schema if it exists, otherwise creates one.
       [-h] [-i INVOCATION] [-w] descriptor

positional arguments:
  descriptor            The Boutiques descriptor as a JSON file, JSON string
                        or Zenodo ID (prefixed by 'zenodo.').

optional arguments:
  -h, --help            show this help message and exit
  -i INVOCATION, --invocation INVOCATION
                        Input values in a JSON file or as a JSON object to be
                        validated against the invocation schema.
  -w, --write-schema    If descriptor doesn't have an invocation schema,
                        creates one and writes it to the descriptor file


**invocation**
==============

.. argparse::
    :module: bosh
    :func: parser_invocation
    :prog: bosh invocation
