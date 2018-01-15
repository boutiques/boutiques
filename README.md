<img src="http://boutiques.github.io/images/logo.png" width="150" alt="Boutiques logo"/>

# Boutiques

[![DOI](https://zenodo.org/badge/32616811.svg)](https://zenodo.org/badge/latestdoi/32616811)
[![PyPI](https://img.shields.io/pypi/v/boutiques.svg)](https://pypi.python.org/pypi/boutiques)
[![PyPI](https://img.shields.io/pypi/pyversions/boutiques.svg)](https://pypi.python.org/pypi/boutiques)
[![Build Status](https://travis-ci.org/boutiques/boutiques.svg?branch=develop)](https://travis-ci.org/boutiques/boutiques)
[![Coverage Status](https://coveralls.io/repos/github/boutiques/boutiques/badge.svg?branch=develop)](https://coveralls.io/github/boutiques/boutiques?branch=develop)

Boutiques is a cross-platform descriptive command-line framework for applications.

# The Power of Boutiques Tools

While the Boutiques framework enables a descriptive representation of command-line utilities and informs users of their usage,
the Boutiques Python tool provides users with functionality to perform a variety of operations on these descriptors.

## Installation

Simple! Just open your favourite terminal and type:

    $ pip install boutiques

Alongside installing the Boutiques package, this will also ensure the dependencies are installed: `simplejson`, `jsonschema`,
`gitpython`, and `pygithub`. 


## Command-Line API

The command-line API for Boutiques can be accessed through your new favourite command, ***`bosh`***. The Boutiques Shell (`bosh`)
provides an access point to all of the tools wrapped within Boutiques and has some `--help` text to keep you moving forward if
you feel like you're getting stuck. Let's consider a few common use-cases...

### Import Your Tool

If you're in the lucky set of people with a Boutiques descriptor from a previous schema iteration (such as `0.4`), or you have a
[BIDS app](http://bids-apps.neuroimaging.io), you can easily make yourself a descriptor from the command-line. For instance, let's
say you have a BIDS app at `/awesome/app/`, you would run:

    $ bosh import bids descriptor.json /awesome/app/

Very exciting, you now have a Boutiques descriptor for your app! If you aren't in one of those unique cases, unfortunately you'll
still need to generate your descriptor by hand according to the [schema](./tools/python/boutiques/schema/descriptor.schema.json).

### Validation

You just created a Boutiques descriptor (compliant with the [schema](./tools/python/boutiques/schema/descriptor.schema.json), of course)
named `descriptor.json` - Congratulations! Now, you need to quickly validate it to make sure that you didn't accidentally break any rules
in this defintion (like requiring a "flag" input). You can validate your schema like this:

    $ bosh validate descriptor.json

Depending on the status of your descriptor, `bosh` will either tell you it's A-OK or tell you where the problems are and what you
should fix. If you want to know more about some extra options packed into this validator, you can check them with `bosh validate -h`,
as one may expect.

### Simulate Execution

Now that you've got a valid descriptor, you need to make sure it is actually describing *your* tool and command-line. One of the easiest
ways to do this is by simulating inputs for fake executions of your tool. You can do this using the `exec` function in `bosh`:

    $ bosh exec simulate descriptor.json -r -n 5

You just simulated 5 sets of random inputs which were dumped to our terminal for you to validate. If anything seems fishy, you can update
your descriptor and ensure you're describing the command-line you want. If you had a particular set of inputs in mind, you could pass them
in with the `-i` flag rather than using the `-r` and `-n` flags. Again, as I'm sure you've guessed, you can learn more here with
`bosh exec simulate -h`.

### Launch Your Tool

Your descriptor has now been vetted both by the validator and simulation to describe meaningful command-lines for your tool - now it's time
to put it to work! You can also use the `exec` function to launch an analysis, provided you've described your inputs in `inputs.json` with the
matching key-value pairs as in your descriptor (this is called the `invocationSchema`, which you can also generate and learn about with
`bosh invocation`). One catch: we assume you have [Docker](https://docker.com) or [Singularity](https://singularity.lbl.gov) installed. A fair
assumption, nowadays? We hope so:

    $ bosh exec launch descriptor.json inputs.json

You just launched your tool! You should be seeing outputs to your terminal, and by default your current working directory will be mounted to the
container. You can mount more volumes with `-v` (consistent with Docker), and see what other options are available, such as switching users in
the container, through the usual help menu, `bosh exec launch -h`.

### Publish Your Tool

Congratulations on successfully running your analysis! So excited about your tool, you now want to share this descriptor with the world. This is
the step which requires our GitHub libraries for Python which you got in the installation above - we're going to make a fork of the
[NeuroLinks](https://brainhack101.github.io/neurolinks) repository, add your tool, and get everying queued up for you to submit a Pull Request
back with the brand new addition. There is a fair bit of metadata we'll collect here, but the basics will be run with the following, assuming
your descriptor lives in a Git-repo available at `/utility/belt/`, your name is `Batman`, and your tool lives at the url `http://thebatcave.io`
(sorry to anyone who owns this url...):

    $ bosh publish /utility/belt/ Batman http://thebatcave.io

Your tool is now being shared in a packaged and fully described fashion, making it easier than ever to reproduce and extend your work! As always,
learn more about this feature with `bosh publish -h`.

## Python API

Now that you've spent all that time learning the command-line API, we've got some good news for you: you already know the Python API, too. The
interfaces are entirely consistent with those exposed on the command-line, so you just need to do the following, to say, validate your schema:

    > import boutiques
    > boutiques.validate('descriptor.json')

Whether you're working from the shell or a Python script, `bosh` will treat you exactly the same.

# Contributing

Excited by the project and want to get involved?! *Please* check out our [contributing guide](./CONTRIBUTING.md), and look through the
[issues](https://github.com/boutiques/boutiques/issues/) (in particular, those tagged with
"[beginner](https://github.com/boutiques/boutiques/issues?utf8=%E2%9C%93&q=is%3Aissue%20is%3Aopen%20label%3Abeginner)") to start seeing where
you can lend a hand. We look forward to approving your amazing contributions!

