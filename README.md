<img src="http://boutiques.github.io/images/logo.png" width="150" alt="Boutiques logo"/>

# Boutiques

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/52fc5590446c4d1eb6626302b491ac3d)](https://app.codacy.com/gh/boutiques/boutiques?utm_source=github.com&utm_medium=referral&utm_content=boutiques/boutiques&utm_campaign=Badge_Grade_Settings)
[![DOI](https://zenodo.org/badge/32616811.svg)](https://zenodo.org/badge/latestdoi/32616811)
[![PyPI](https://img.shields.io/pypi/v/boutiques.svg)](https://pypi.python.org/pypi/boutiques)
[![PyPI](https://img.shields.io/pypi/pyversions/boutiques.svg)](https://pypi.python.org/pypi/boutiques)
[![Build Status](https://travis-ci.org/boutiques/boutiques.svg?branch=develop)](https://travis-ci.org/boutiques/boutiques)
[![Coverage Status](https://coveralls.io/repos/github/boutiques/boutiques/badge.svg?branch=develop)](https://coveralls.io/github/boutiques/boutiques?branch=develop)

Boutiques is a cross-platform descriptive command-line framework for applications.

## The Power of Boutiques Tools

Boutiques is a framework to make data analysis tools Findable Accessible
Interoperable and Reusable (FAIR). An overview of the framework and its
capabilities is available
[here](https://figshare.com/articles/fair-pipelines-poster_pdf/8143241),
and a more complete description is
[here](https://academic.oup.com/gigascience/article/7/5/giy016/4951979).

## Installation

Simple! Just open your favourite terminal and type:

    $ pip install boutiques

Alongside installing the Boutiques package, this will also ensure the dependencies are installed: `simplejson`, `jsonschema`,
`requests`, `pytest`, `termcolor`, `oyaml`, `tabulate` and `mock`.

If you want the latest changes that aren't officially released yet, you can also install directly from GitHub:

    $ pip install "git+https://github.com/boutiques/boutiques@develop#egg=boutiques"

## Tutorial

Our
[tutorial](https://nbviewer.jupyter.org/github/boutiques/tutorial/blob/master/notebooks/boutiques-tutorial.ipynb)
will introduce you to the main Boutiques features through its command line
and Python APIs. Give it a try!

## Contributing

Excited by the project and want to get involved?! *Please* check out our [contributing guide](./CONTRIBUTING.md), and look through the
[issues](https://github.com/boutiques/boutiques/issues/) (in particular, those tagged with
"[good first issue](https://github.com/boutiques/boutiques/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)") to start seeing where
you can lend a hand. We look forward to approving your amazing contributions!

## Examples
We have a [simple](https://github.com/boutiques/boutiques/tree/master/boutiques/schema/examples/example3) and a [complex](https://github.com/boutiques/boutiques/tree/master/boutiques/schema/examples/example1) Boutiques descriptor to help you get started with your own descriptor.