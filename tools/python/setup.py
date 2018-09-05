import sys
from setuptools import setup
import sys

VERSION = "0.5.13"
DEPS = [
         "simplejson",
         "requests",
         "pytest",
         "termcolor",
         "pyyaml"
       ]

# jsonschema 2.6 doesn't support Python 2.6
# and unittest2 is a backport of Python 2.7's 'unittest to 2.6
if sys.version_info < (2, 7):
    DEPS.append("unittest2")
    DEPS.append("jsonschema==2.5.1")
else:
    DEPS.append("jsonschema")

setup(name="boutiques",
      version=VERSION,
      description="Schema for describing bash command-line tools",
      long_description=open("./README.rst").read(),
      url="http://github.com/boutiques/boutiques",
      author="Tristan Glatard, Gregory Kiar",
      author_email="tristan.glatard@concordia.ca, gkiar07@gmail.com",
      classifiers=[
                "Programming Language :: Python",
                "Programming Language :: Python :: 2",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 2.6",
                "Programming Language :: Python :: 2.7",
                "Programming Language :: Python :: 3.4",
                "Programming Language :: Python :: 3.5",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: Implementation :: PyPy",
                "License :: OSI Approved :: MIT License",
                "Topic :: Software Development :: Libraries :: Python Modules",
                "Operating System :: OS Independent",
                "Natural Language :: English"
                  ],
      license="MIT",
      packages=["boutiques"],
      include_package_data=True,
      test_suite="pytest",
      tests_require=["pytest"],
      setup_requires=DEPS,
      install_requires=DEPS,
      entry_points=  {
        "console_scripts": [
            "bosh=boutiques.bosh:bosh",
        ]
      },
      zip_safe=False)
