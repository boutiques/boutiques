from boutiques.bosh import bosh
from unittest import TestCase


class TestSearch(TestCase):

    def test_search_all(self):
        results = bosh(["search"])
        assert(len(results) > 0)
        assert(list(results[0].keys()) == ["ID", "TITLE", "DESCRIPTION",
                                           "DOWNLOADS"])

    def test_search_query(self):
        results = bosh(["search", "ICA_AROMA"])
        assert(len(results) > 0)
        assert("ICA_AROMA" in results[0]["TITLE"])

    def test_search_verbose(self):
        results = bosh(["search", "-v"])
        assert(len(results) > 0)
        assert(list(results[0].keys()) == ["ID", "TITLE", "DESCRIPTION",
                                           "DOWNLOADS", "AUTHOR", "VERSION",
                                           "DOI", "SCHEMA VERSION",
                                           "CONTAINER", "TAGS"])

    def test_search_specify_max_results(self):
        results = bosh(["search", "--sandbox", "-m", "20"])
        assert(len(results) == 20)

    def test_search_sorts_by_num_downloads(self):
        results = bosh(["search"])
        downloads = []
        for r in results:
            downloads.append(r["DOWNLOADS"])
        assert(all(downloads[i] >= downloads[i+1]
               for i in range(len(downloads)-1)))

    def test_search_truncates_long_text(self):
        results = bosh(["search"])
        for r in results:
            for k, v in r.items():
                assert(len(str(v)) <= 43)

    def test_search_no_trunc(self):
        results = bosh(["search", "--no-trunc"])
        has_no_trunc = False
        for r in results:
            for k, v in r.items():
                if len(str(v)) > 43:
                    has_no_trunc = True
                    break
            else:
                continue
            break
        assert(has_no_trunc)
