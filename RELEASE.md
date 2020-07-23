# Release process

1. Bump version number in `boutiques/__version__.py`
2. If schema was modified, re-generate `boutiques/schema/README.md` using [jsonschema2md](https://github.com/adobe/jsonschema2md)
   ```
   git clone https://github.com/adobe/jsonschema2md.git
   cd jsonschema2md
   npm link
   cd ..
   jsonschema2md -d ./boutiques/schema/descriptor.schema.json -v 04
   cp out/descriptor.schema.md ./boutiques/schema/README.md
   ```
3. If the `README.md` at the base of this repository was updated, update `./README.rst` using [pandoc](https://pandoc.org/)
   ```
   cp ./README.rst ./README_old.rst
   pandoc --from=markdown --to=rst --output=./README.rst README.md
   # Manually, you may need to replace the links near the top with the badges as specified in the top of the README_old.rst file
   # Once this is done, remove the old copy.
   # rm ./README_old.rst
   ```
4. Merge `develop` in `master`
5. Create tag on GitHub, add release notes 
6. Push to PyPi:
   ```
   python setup.py bdist_wheel --universal
   twine upload dist/*
   ```
7. Install [Sphinx](https://www.sphinx-doc.org/en/master/usage/installation.html) for python 3
8. Generate Bosh API docs
   ```
   cd ./docs
   pip install sphinx-rtd-theme sphinx-argparse
   python argparse_docs.py
   ```
