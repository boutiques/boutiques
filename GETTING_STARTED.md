# Getting Started as a Boutiques Developer

This guide will help you set up your local environment for coding and testing Boutiques.

## 0. Things you'll need
- **A Linux system**. It _may_ be possible to develop Boutiques on Windows, but will likely cause many headaches.
- **Root (sudo) access**. Unless your system already has everything you need installed, you'll need root permission to install new programs.
- **Python**. Boutiques supports any version >= 2.7. It's a good idea to have multiple versions of Python installed (e.g. 2.7 and 3.7) so you can test your code for version compatibility.
- **pip**. Most versions of Python will come with it, but in case you don't have it, instructions to install it are [here](https://pip.pypa.io/en/stable/installing/).
- **Docker**. If you don't already have Docker, follow the [instructions](https://docs.docker.com/install/overview/) to install Docker CE.
- **Singularity**. Follow the instructions [here](https://singularity.lbl.gov/install-linux) to download the latest stable release of Singularity.
- **Git**. If you don't have Git, instructions to install it are [here](https://git-scm.com/download/linux).

## 1. Clone the boutiques repository
- Fork the [Boutiques repository](https://github.com/boutiques/boutiques).
- Clone your fork locally: 
    `git clone https://github.com/<YOUR-GITHUB-USERNAME>/boutiques.git`

## 2. Create a virtual environment
- Install virtualenv:
  `sudo pip install virtualenv`
- Create a virtual envrionment in the Python tools root directory:
  `cd boutiques/tools/python`
  `virtualenv env`
- Use the environment whenever you work on Boutiques by running:
  `source env/bin/activate`
- Note: if you wish to leave the virtual environment, simply run `deactivate`.

## 3. Install Boutiques, test framework and validation tools
From within your virtual environment in the `boutiques/tools/python` directory:
- Upgrade setuptools: `pip install --upgrade setuptools`
- Install pytest and pycodestyle: `pip install pytest pycodestyle`
  - pytest is a unit testing framework for Python.
  - pycodestyle checks if your code conforms to Python style conventions.
- Install jsonlint: `npm install jsonlint -g` 
  - In case you don't have Node installed, instructions to install it are [here](https://www.npmjs.com/get-npm).
  - jsonlint is a tool to validate JSON files. 
- Install Boutiques: `pip install boutiques` or just `pip install .`
- Note that pytest, pycodestyle and jsonlint are all used by Travis CI, but it's best practice to test and validate your code locally before pushing it!

## 4. Build the container images needed for testing
- Certain test cases involve example descriptors that use a Docker or Singularity container iamge. These images are not available on DockerHub or SingularityHub and must be built locally.
- From the `boutiques/tools/python` directory, build the example Docker image with the following command:
  `docker build -t boutiques/example1:test ./boutiques/schema/examples/example1`
- Once the Docker image is built, convert it to a Singularity image. Again, from within the `boutiques/python/tools` directory:
  - `docker run -v /var/run/docker.sock:/var/run/docker.sock -v ${HOME}:/output --privileged -t --rm singularityware/docker2singularity boutiques/example1:test`
  - `IMGNAME=$(ls $HOME/boutiques_example1_test*.simg)`
  - `mv ${IMGNAME} ./boutiques-example1-test.simg`
  - Your directory should now contain a ~70MB file called `boutiques_example1_test.simg`.
 
## 5. Try it out!
- Run `pytest` in the `boutiques/tools/python` directory to run all tests.
- Run an individual test file with `pytest boutiques/tests/test_<something>.py`
- Validate your code style by running:
  `pycodestyle --max-line-length=80 boutiques/*.py boutiques/tests/*.py`
- Validate changes to the Boutiques JSON schema by running:
  `jsonlint -q boutiques/schema/descriptor.schema.json`

## Things to Note
- Whenever you make changes to the code and wish to test the `bosh` command-line interface, you must reinstall Boutiques (`pip install boutiques` or `pip install .`). Otherwise, you will be running Boutiques with the old code.

## Ready to code?
- See the [Contributing Guide](https://github.com/boutiques/boutiques/blob/master/CONTRIBUTING.md) for instructions on how to contribute to the repository.