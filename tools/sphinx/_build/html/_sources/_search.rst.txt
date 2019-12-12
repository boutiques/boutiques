Python API
==========
usage: Search Zenodo for Boutiques descriptors. When no term is supplied, will search for all descriptors.
       [-h] [-v] [--sandbox] [-m MAX] [-nt] [-e] [query]

positional arguments:
  query              Search query

optional arguments:
  -h, --help         show this help message and exit
  -v, --verbose      Print information messages
  --sandbox          search Zenodo's sandbox instead of production server.
                     Recommended for tests.
  -m MAX, --max MAX  Specify the maximum number of results to be returned.
                     Default is 10.
  -nt, --no-trunc    Do not truncate long tool descriptions.
  -e, --exact        Only return results containing the exact query.


**search**
==========

.. argparse::
    :module: bosh
    :func: parser_search
    :prog: bosh search
