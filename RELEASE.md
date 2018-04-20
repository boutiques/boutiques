# Release process

1. Bump version number in `setup.py`
2. If schema was modified, re-generate `schema/README.md` using [jsonschema2md](https://github.com/adobe/jsonschema2md)
   ```
   git clone https://github.com/adobe/jsonschema2md.git
   cd jsonschema2md
   npm link
   cd ..
   jsonschema2md -d ./tools/python/boutiques/schema/descriptor.schema.json
   cp out/descripor.schema.md schema/README.md
   ```
3. Merge `develop` in `master`
4. Create tag on GitHub, add release notes 
5. Push to PyPi:
   ```
   python setup.py bdist_wheel --universal`
   twine upload dist/*
   ```
