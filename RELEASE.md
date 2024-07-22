# Release process

1.  If schema was modified, re-generate `boutiques/schema/README.md` using [jsonschema2md](https://github.com/adobe/jsonschema2md)
    ```bash
    git clone https://github.com/adobe/jsonschema2md.git
    cd jsonschema2md
    npm link
    cd ..
    jsonschema2md -d ./boutiques/schema/descriptor.schema.json -v 04
    cp out/descriptor.schema.md ./boutiques/schema/README.md
    ```

1.  If the `README.md` at the base of this repository was updated, update `./README.rst` using [pandoc](https://pandoc.org/)
    ```bash
    cp ./README.rst ./README_old.rst
    pandoc --from=markdown --to=rst --output=./README.rst README.md
    # Manually, you may need to replace the links near the top with the badges as specified in the top of the README_old.rst file
    # Once this is done, remove the old copy.
    # rm ./README_old.rst
    ```

1.  Merge `develop` in `master`

1.  Create X.Y.Z tag on GitHub, add release notes

1.  Get tags from github and checkout the last version:
    ```bash
    git pull --all
    git checkout X.Y.Z
    ```

1.  Push to PyPi:
    ```bash
    pip install build twine
    python -m build
    twine check dist/*
    twine upload dist/*
    ```

1.  Generate Bosh API docs
    ```bash
    pip install ".[doc]"
    cd ./docs
    python argparse_docs.py
    ```
