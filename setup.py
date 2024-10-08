import sys
from setuptools import setup
import os.path as op


# Loads version information from file inside package. This allows the package
# itself to be aware of its version.
verfile = op.join("boutiques", "__version__.py")
with open(verfile) as fhandle:
    exec(fhandle.read())

DEPS = [
         "simplejson",
         "termcolor",
         "jsonschema",
         "tabulate",
]
eDEPS = {
    "all": [
         "oyaml",
         "toml",
         "docopt",
         "pytest",
         "pytest-runner",
         "coverage",
         "nexus-sdk",
         "requests",
         "mock"
    ]
}

setup(name="boutiques",
      version=VERSION,
      description="Schema for describing bash command-line tools",
      long_description=open("./README.rst", encoding="utf-8").read(),
      url="http://github.com/boutiques/boutiques",
      author="Tristan Glatard, Gregory Kiar",
      author_email="tristan.glatard@concordia.ca, gkiar07@gmail.com",
      classifiers=[
                "Programming Language :: Python",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.5",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
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
      extras_require=eDEPS,
      install_requires=DEPS,
      entry_points={
        "console_scripts": [
            "bosh=boutiques.bosh:bosh",
        ]
      },
      zip_safe=False)
