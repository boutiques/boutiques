Python API
==========
usage: Manage execution data collection. [--help] {inspect,publish,delete}

positional arguments:
  {inspect,publish,delete}
                        Manage execution data records. Inspect: displays the
                        unpublished records currently in the cache. Publish:
                        publishes contents of cache to Zenodo as a public data
                        set. Requires a Zenodo access token, see
                        http://developers.zenodo.org/#authentication. Delete:
                        remove one or more records from the cache.

optional arguments:
  --help, -h            show this help message and exit


**data**
========

.. argparse::
    :module: bosh
    :func: parser_data
    :prog: bosh data

**data delete**
---------------

.. argparse::
    :module: bosh
    :func: parser_dataDelete
    :prog: bosh data delete

**data inspect**
----------------

.. argparse::
    :module: bosh
    :func: parser_dataInspect
    :prog: bosh data inspect

**data publish**
----------------

.. argparse::
    :module: bosh
    :func: parser_dataPublish
    :prog: bosh data publish
