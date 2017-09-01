Once authenticated, and ensuring you have `twine` and `wheel` installed, run:

```
python setup.py sdist
python setup.py bdist_wheel
twine upload dist/boutiques-....tar.gz # use correct version
twine upload dist/boutiques-....whl    # use correct version
```
