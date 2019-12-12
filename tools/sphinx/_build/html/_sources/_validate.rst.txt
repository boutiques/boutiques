Python API
==========
usage: Boutiques descriptor validator [-h] [--bids] [--format] descriptor

positional arguments:
  descriptor    The Boutiques descriptor as a JSON file, JSON string or Zenodo
                ID (prefixed by 'zenodo.').

optional arguments:
  -h, --help    show this help message and exit
  --bids, -b    Flag indicating if descriptor is a BIDS app
  --format, -f  If descriptor is valid, rewrite it with sorted keys.


**validate**
============

.. argparse::
    :module: bosh
    :func: parser_validate
    :prog: bosh validate
