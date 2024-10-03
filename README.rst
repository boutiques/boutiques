Boutiques
=========

-.. image:: https://zenodo.org/badge/32616811.svg
-    :target: https://zenodo.org/badge/latestdoi/32616811
-.. image:: https://img.shields.io/pypi/v/boutiques.svg
-    :target: https://pypi.python.org/pypi/boutiques
-.. image:: https://img.shields.io/pypi/pyversions/boutiques.svg
-    :target: https://pypi.python.org/pypi/boutiques
-.. image:: https://travis-ci.org/boutiques/boutiques.svg?branch=develop
-    :target: https://travis-ci.org/boutiques/boutiques
-.. image:: https://coveralls.io/repos/github/boutiques/boutiques/badge.svg?branch=develop
-    :target: https://coveralls.io/github/boutiques/boutiques?branch=develop

Boutiques is a cross-platform descriptive command-line framework for
applications.

The Power of Boutiques Tools
----------------------------

Boutiques is a framework to make data analysis tools Findable Accessible
Interoperable and Reusable (FAIR). An overview of the framework and its
capabilities is available
`here <https://figshare.com/articles/fair-pipelines-poster_pdf/8143241>`__,
and a more complete description is
`here <https://academic.oup.com/gigascience/article/7/5/giy016/4951979>`__.

Installation
------------

Simple! Just open your favourite terminal and type:

::

   $ pip install boutiques

Alongside installing the Boutiques package, this will also ensure the
dependencies are installed for basic functionality: ``simplejson``,
``jsonschema``, ``termcolor``, and ``tabulate``. With this, you’ll be
able to validate and run your tools through Boutiques. For full
functionality, you can install the library as follows:

::

   $ pip install boutiques[all]

This will add some more dependencies, and let you use all of the
features: ``requests``, ``pytest``, ``termcolor``, ``oyaml``,
``tabulate`` and ``mock``. Now you’ll also be able to search for tools
and publish your own and records from when you ran your tool!

If you want the latest changes that aren’t officially released yet, you
can also install directly from GitHub:

::

   $ pip install "git+https://github.com/boutiques/boutiques@develop#egg=boutiques"

Tutorial
--------

Our
`tutorial <https://nbviewer.jupyter.org/github/boutiques/tutorial/blob/master/notebooks/boutiques-tutorial.ipynb>`__
will introduce you to the main Boutiques features through its command
line and Python APIs. Give it a try!

Contributing
------------

Excited by the project and want to get involved?! *Please* check out our
`contributing guide <./CONTRIBUTING.md>`__, and look through the
`issues <https://github.com/boutiques/boutiques/issues/>`__ (in
particular, those tagged with “`good first
issue <https://github.com/boutiques/boutiques/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22>`__”)
to start seeing where you can lend a hand. We look forward to approving
your amazing contributions!

Examples
--------

We have a
`simple <https://github.com/boutiques/boutiques/tree/master/boutiques/schema/examples/example3>`__
and a
`complex <https://github.com/boutiques/boutiques/tree/master/boutiques/schema/examples/example1>`__
Boutiques descriptor to help you get started with your own descriptor.

.. |Codacy Badge| image:: https://api.codacy.com/project/badge/Grade/52fc5590446c4d1eb6626302b491ac3d
   :target: https://app.codacy.com/gh/boutiques/boutiques?utm_source=github.com&utm_medium=referral&utm_content=boutiques/boutiques&utm_campaign=Badge_Grade_Settings
.. |DOI| image:: https://zenodo.org/badge/32616811.svg
   :target: https://zenodo.org/badge/latestdoi/32616811
.. |PyPI| image:: https://img.shields.io/pypi/v/boutiques.svg
   :target: https://pypi.python.org/pypi/boutiques
.. |image1| image:: https://img.shields.io/pypi/pyversions/boutiques.svg
   :target: https://pypi.python.org/pypi/boutiques
.. |Build Status| image:: https://travis-ci.org/boutiques/boutiques.svg?branch=develop
   :target: https://travis-ci.org/boutiques/boutiques
.. |Coverage Status| image:: https://coveralls.io/repos/github/boutiques/boutiques/badge.svg?branch=develop
   :target: https://coveralls.io/github/boutiques/boutiques?branch=develop
