Python API
==========
usage: Boutiques descriptor creator [-h] [--docker-image DOCKER_IMAGE]
                                    [--use-singularity]
                                    descriptor

positional arguments:
  descriptor            Output file to store descriptor in.

optional arguments:
  -h, --help            show this help message and exit
  --docker-image DOCKER_IMAGE, -d DOCKER_IMAGE
                        Name of Docker image on DockerHub.
  --use-singularity, -u
                        When --docker-image is used. Specify to use
                        singularity to run it.


**create**
==========

.. argparse::
    :module: bosh
    :func: parser_create
    :prog: bosh create
