# Getting Started as a Boutiques Developer

This guide will help you set up your local environment for coding and testing Boutiques.

## 0. Things you'll need
- **A Linux shell**. It _may_ be possible to develop Boutiques on Windows, but will likely cause many headaches (if you successfully develop for Boutiques on Windows, please update this guide with details!).
- **Git**. If you don't have Git, instructions to install it are [here](https://git-scm.com/download/linux).
- **Python**. Boutiques supports any version >= 3.5.
- **pip**. Most versions of Python will come with it, but in case you don't have it, instructions to install it are [here](https://pip.pypa.io/en/stable/installing/).
- **Docker or Singularity**. Depending on the tools you plan to work with and where they are installed, you'll want to have either Docker or Singularity installed (ideally both).
  - To install Docker, follow the  [instructions](https://docs.docker.com/install/overview/) to install Docker CE.
  - To install Singularity, follow the [instructions](https://singularity.lbl.gov/install-linux) to download the latest stable release of Singularity.
- **Root (sudo) access**. If your system doesn't already have all of the above installed, you'll need root permission to install new programs.

## 1. Clone the boutiques repository
- Fork the [Boutiques repository](https://github.com/boutiques/boutiques).
- Clone your fork locally: 
    - `git clone https://github.com/<YOUR-GITHUB-USERNAME>/boutiques.git`
    - Or, if you installed your SSH keys on GitHub:  `git@github.com:boutiques/boutiques.git`

## 2. Create a virtual environment
- Install virtualenv:
  - `pip install --user virtualenv`
- Create a virtual environment in the Python tools root directory:
  - `cd boutiques/tools/python`
  - `mkdir env`
  - `virtualenv env/boutiques -p python3.6`  (replace python3.6 with the executable for the version of Python you wish to use)
- Use the environment whenever you work on Boutiques by running:
  - `source env/boutiques/bin/activate`
- Note: if you wish to leave the virtual environment, simply run `deactivate`.

## 3. Install Boutiques, test framework and validation tools
From within your virtual environment in the `boutiques/tools/python` directory:
- Upgrade setuptools: `pip install --upgrade setuptools`
- Install pytest, pytest-runner and pycodestyle: `pip install pytest pytest-runner pycodestyle`
  - pytest is a unit testing framework for Python.
  - pycodestyle checks if your code conforms to Python style conventions.
- Install jsonlint: `npm install jsonlint -g` 
  - In case you don't have Node installed, instructions to install it are [here](https://www.npmjs.com/get-npm).
  - jsonlint is a tool to validate JSON files. 
- Install Boutiques: `pip install -e .`
- Note that pytest, pycodestyle and jsonlint are all used by Travis CI, but it's best practice to test and validate your code locally before pushing it!

## 4. Build the container images needed for testing
- Certain test cases involve example descriptors that use a Docker or Singularity container image. These images are not available on DockerHub or SingularityHub and must be built locally.
- From the `boutiques/tools/python` directory, build the example Docker image with the following command:
  - Note: skip the following step if you do not have Docker installed.
  - `docker build -t boutiques/example1:test ./boutiques/schema/examples/example1`
- Once the Docker image is built, convert it to a Singularity image. Again, from within the `boutiques/tools/python` directory:
  - Note: skip the following steps if you do not have Singularity installed.
  - `docker run -v /var/run/docker.sock:/var/run/docker.sock -v ${HOME}:/output --privileged -t --rm singularityware/docker2singularity boutiques/example1:test`
  - `IMGNAME=$(ls $HOME/boutiques_example1_test*.simg)`
  - `mv ${IMGNAME} ./boutiques-example1-test.simg`
  - Your directory should now contain a ~70MB file called `boutiques_example1_test.simg`.
 
## 5. Try it out!
- Run `pytest` in the `boutiques/tools/python` directory to run all tests.
- Run an individual test file with `pytest boutiques/tests/test_<something>.py`
- Validate your code style by running:
  - `pycodestyle --max-line-length=80 boutiques/*.py boutiques/tests/*.py`
- Validate changes to the Boutiques JSON schema by running:
  - `jsonlint -q boutiques/schema/descriptor.schema.json`

## Ready to code?
- See the [Contributing Guide](https://github.com/boutiques/boutiques/blob/master/CONTRIBUTING.md) for instructions on how to contribute to the repository.
