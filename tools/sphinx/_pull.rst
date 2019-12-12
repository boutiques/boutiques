Python API
==========
usage: Ensures that Zenodo descriptors are locally cached, downloading them if needed.
       [-h] [-v] [--sandbox] zids [zids ...]

positional arguments:
  zids           One or more Zenodo IDs for the descriptor(s) to pull,
                 prefixed by 'zenodo.', e.g. zenodo.123456 zenodo.123457

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Print information messages
  --sandbox      pull from Zenodo's sandbox instead of production server.
                 Recommended for tests.


**pull**
========

.. argparse::
    :module: bosh
    :func: parser_pull
    :prog: bosh pull
