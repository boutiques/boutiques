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
`requests`, `pytest`, `termcolor`, `pyyaml`, `tabulate` and `mock`. 

If you want the latest changes that aren't officially released yet, you can also install directly from GitHub:

    $ pip install "git+https://github.com/boutiques/boutiques@develop#egg=boutiques&subdirectory=tools/python"

## Command-Line API

The command-line API for Boutiques can be accessed through your new favourite command, ***`bosh`***. The Boutiques Shell (`bosh`)
provides an access point to all of the tools wrapped within Boutiques and has some `--help` text to keep you moving forward if
you feel like you're getting stuck. Let's consider a few common use-cases...

### Search For Tools

Perhaps someone has already described the tool you are looking for and 
you could reuse their work. For instance, if you are looking for a tool 
from the FSL suite, try:

    $ bosh search fsl

Search returns a list of identifiers for tools matching your query. You 
can use these identifiers in any `bosh` command transparently. Even 
better, these identifiers are [Digital Object Identifiers](https://www.doi.org)
hosted on [Zenodo](https://zenodo.org/), they will never change and can't
be deleted!

### Import Your Tool

If you're in the lucky set of people with a Boutiques descriptor from a previous schema iteration (such as `0.4`), or you have a
[BIDS app](http://bids-apps.neuroimaging.io), you can easily make yourself a descriptor from the command-line. For instance, let's
say you have a BIDS app at `/awesome/app/`, you would run:

    $ bosh import bids descriptor.json /awesome/app/

Very exciting, you now have a Boutiques descriptor for your app! If you aren't in one of those unique cases, unfortunately you'll
still need to generate your descriptor by hand according to the [schema](./tools/python/boutiques/schema/descriptor.schema.json).

### Create a New Descriptor

There are two additional ways to get you started with creating Boutiques descriptors, both wrapped up in the "create" module
of Boutiques. First, if you just want an example descriptor that shows many of the properties you can later set in Boutiques, you
should use the command line interface:

    $ bosh create my-new-descriptor.json

However, if you want a bit more of a head start and your tool is built in Python using the `argparse` library, we can help more!
In the Python script with your argparser defined, simply add the following lines to get yourself a minimal corresponding descriptor:

    import boutiques.creator as bc
    newDescriptor = bc.CreateDescriptor(myparser, execname="/command/to/run/exec")
    newDescriptor.save("my-new-descriptor.json")

There are additional custom arguments which can be supplied to this script, such as tags for your tool. It is also worth noting that
no interpretation of output files is attempted by this tool, so your descriptor could certainly be enhanced by addind these and other
features available through Boutiques, such as tests, tags, error codes, groups, and container images.

Once you've created your descriptor this way you can translate your arguments to a Boutiques-style invocation using the following
code block on runtime:

    args = myparser.parse_args()
    invoc = newDescriptor.createInvocation(args)

    # Then, if you want to save them to a file...
    import json
    with open('my-inputs.json', 'w') as fhandle:
        fhandle.write(json.dumps(invoc, indent=4))


### Validation

You just created a Boutiques descriptor (compliant with the [schema](./tools/python/boutiques/schema/descriptor.schema.json), of course)
named `descriptor.json` - Congratulations! Now, you need to quickly validate it to make sure that you didn't accidentally break any rules
in this definition (like requiring a "flag" input). You can validate your schema like this:

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
to put it to work! You can also use the `exec` function to launch an analysis, provided you've described your inputs in `invocation.json` with the
matching key-value pairs as in your descriptor (this is called the `invocationSchema`, which you can also generate and learn about with
`bosh invocation`). One catch: we assume you have [Docker](https://docker.com) or [Singularity](https://singularity.lbl.gov) installed. A fair
assumption, nowadays? We hope so:

    $ bosh exec launch descriptor.json invocation.json

You just launched your tool! You should be seeing outputs to your terminal, and by default your current working directory will be mounted to the
container. You can mount more volumes with `-v` (consistent with Docker), and see what other options are available, such as switching users in
the container, through the usual help menu, `bosh exec launch -h`.

### Test Your Tool

You may now want to write a test for your descriptor, so that everyone
using it could check that it produces correct results. This can be
done by extending the tool descriptor with a `tests` property. For
instance, the description below would test if the execution of the specified invocation returns with exit code 0 and produces a file in output `logfile` with
the right MD5 hash.
```
"tests": [
        {
	     "name": "test1",
	     "invocation": {
                "config_num": 4,
                "enum_input": "val1",
                "file_input": "/tests/image.nii.gz",
                "list_int_input": [
                    1,
                    2,
                    3
                ],
                "str_input": [
                    "foo",
                    "bar"
                ]
            },
            "assertions": {
                "exit-code": 0,
                "output-files": [
                    {
                        "id": "logfile",
                        "md5-reference": "0868f0b9bf25d4e6a611be8f02a880b5"
                    }
                ]
            }
    }
]
```
You can then test your descriptor by simply typing:

    $ bosh test descriptor.json

### Evaluate Your Usage

If you've been using your tool and forget what exactly that output file will be named, or if it's optional, but find re-reading the descriptor a
bit cumbersome, you should just evaluate your invocation! If we wanted to check the location of our output corresponding to the id `my_batmobile`,
or which of our inputs are numbers and optional, we could do the following two queries, respectively:

    $ bosh evaluate descriptor.json invocation.json output-files/id=my_batmobile inputs/type=Number,optional=True
    [{"my_batmobile": "/the/batcave/batmobile.car"}, {"bad_guys": "0", "times_saved_gotham": "5000"}]

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

### Execution Records

Want to check up on what happened during a previous analysis? The details of each execution are captured and recorded in a publicly safe format so that 
you can review past analysis runs. These records are stored in the Boutiques cache and capture each executions' descriptor, invocation and output results.
Input and output file hashes are included to easily compare results between different analyses.

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

