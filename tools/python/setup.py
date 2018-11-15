import sys
from setuptools import setup
import sys

VERSION = "0.5.15"
DEPS = [
         "simplejson",
         "requests",
         "pytest",
         "termcolor",
         "pyyaml",
         "jsonschema",
	       "tabulate"
       ]

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
