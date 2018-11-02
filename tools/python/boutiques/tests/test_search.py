from boutiques.bosh import bosh
from unittest import TestCase


class TestSearch(TestCase):

    def test_search_all(self):
        results = bosh(["search"])
        assert(len(results) > 0)

    def test_search_query(self):
        results = bosh(["search", "ICA_AROMA"])
        assert(len(results) > 0)
        assert("ICA_AROMA" in results[0]["TITLE"])
