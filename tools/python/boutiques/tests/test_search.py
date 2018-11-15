from boutiques.bosh import bosh
from unittest import TestCase


class TestSearch(TestCase):

    def test_search_all(self):
        results = bosh(["search"])
        assert(len(results) > 0)
        assert(list(results[0].keys()) == ["ID", "TITLE", "DESCRIPTION"])

    def test_search_query(self):
        results = bosh(["search", "ICA_AROMA"])
        assert(len(results) > 0)
        assert("ICA_AROMA" in results[0]["TITLE"])

    def test_search_verbose(self):
        results = bosh(["search", "-v"])
        assert(len(results) > 0)
        assert(list(results[0].keys()) == ["ID", "TITLE", "DESCRIPTION",
                                           "AUTHOR", "VERSION", "DOI",
                                           "SCHEMA VERSION", "CONTAINER",
                                           "TAGS"])

    def test_search_specify_max_results(self):
        results = bosh(["search", "--sandbox", "-m", "20"])
        assert(len(results) == 20)
