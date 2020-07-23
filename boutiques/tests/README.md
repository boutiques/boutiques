## Boutiques Tests

### Directories
- One asset directory for each Python test script (ex: [./bids/](https://github.com/boutiques/boutiques/tree/master/boutiques/tests/bids/) for [test_bids.py](https://github.com/boutiques/boutiques/blob/master/boutiques/tests/test_bids.py))
- Use [BaseTest.py](https://github.com/boutiques/boutiques/blob/master/boutiques/tests/BaseTest.py) functions to setup test directory and access test assets

### Tests
- All test classes extend [BaseTest.py](https://github.com/boutiques/boutiques/blob/master/boutiques/tests/BaseTest.py)
- Use [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html) to cleanup files created during test execution
- [boutiques_mocks.py](https://github.com/boutiques/boutiques/blob/master/boutiques/tests/boutiques_mocks.py) contains general mock functions, specialized mocks are located in test scripts (eg. [mock_get](https://github.com/boutiques/boutiques/blob/master/boutiques/tests/test_deprecate.py))