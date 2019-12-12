Python API
==========
usage: Boutiques publisher [-h] [--sandbox] [--zenodo-token ZENODO_TOKEN]
                           [--no-int] [-v] [-r | --id ID]
                           boutiques_descriptor

A publisher of Boutiques tools in Zenodo (http://zenodo.org). Requires a
Zenodo access token, see http://developers.zenodo.org/#authentication.

positional arguments:
  boutiques_descriptor  local path of the Boutiques descriptor to publish.

optional arguments:
  -h, --help            show this help message and exit
  --sandbox             publish to Zenodo's sandbox instead of production
                        server. Recommended for tests.
  --zenodo-token ZENODO_TOKEN
                        Zenodo API token to use for authentication. If not
                        used, token will be read from configuration file or
                        requested interactively.
  --no-int, -y          disable interactive input.
  -v, --verbose         print information messages.
  -r, --replace         Publish an updated version of an existing record. The
                        descriptor must contain a DOI, which will be replaced
                        with a new one.
  --id ID               Zenodo ID of an existing record you wish to update
                        with a new version, prefixed by 'zenodo.' (e.g.
                        zenodo.123456).


**publish**
===========

.. argparse::
    :module: bosh
    :func: parser_publish
    :prog: bosh publish
