from setuptools import setup

VERSION = "0.5.3"
DEPS = [
         "simplejson",
         "jsonschema",
         "gitpython",
         "PyGithub",
       ]

setup(name="boutiques",
      version=VERSION,
      description="Schema for describing bash command-line tools",
      url="http://github.com/boutiques/boutiques",
      author="Tristan Glatard, Gregory Kiar",
      author_email="tristan.glatard@gmail.com, gkiar07@gmail.com",
      classifiers=[
                "Programming Language :: Python",
                "Programming Language :: Python :: 2",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 2.7",
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
      entry_points = {
        "console_scripts": [
            "bosh=boutiques.bosh:bosh",
        ]
      },
      data_files=[("schema", ["boutiques/schema/descriptor.schema.json"]),
                  ("bids-template", ["boutiques/bids-app-template/template.json"]),
                  ("neurolinks-template", ["boutiques/neurolinks-template/tool.json"]),
                  ("exgood", ["boutiques/schema/examples/good.json"]),
                  ("exinvalid", ["boutiques/schema/examples/invalid.json"]),
                  ("exbidsgood", ["boutiques/schema/examples/bids_good.json"]),
                  ("exbidsbad1", ["boutiques/schema/examples/bids_bad1.json"]),
                  ("exbidsbad2", ["boutiques/schema/examples/bids_bad2.json"]),
                  ("exbad", ["boutiques/schema/examples/bad.json"])],
      zip_safe=False)
