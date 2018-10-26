from boutiques.bosh import bosh
from unittest import TestCase


class TestSearch(TestCase):

    def test_search_all(self):
        results = bosh(["search"])
        assert(results)

    def test_search_query(self):
        results = bosh(["search", "-q", "ICA_AROMA"])
        assert("ICA_AROMA" in results)
