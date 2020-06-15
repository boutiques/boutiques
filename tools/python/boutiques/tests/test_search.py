from boutiques.bosh import bosh
from unittest import TestCase
import mock
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord


def mock_get(query, exact, *args, **kwargs):
    max_results = args[0].split("=")[-1]

    # Long description text to test truncation
    long_description = ("Lorem ipsum dolor sit amet, consectetur adipiscing "
                        "elit, sed do eiusmod tempor incididunt ut labore et "
                        "dolore magna aliqua. Ut enim ad minim veniam, quis "
                        "nostrud exercitation ullamco laboris nisi ut aliquip "
                        "ex ea commodo consequat.")

    mock_records = []
    # Return an arbitrary list of results with length max_results
    if query == "boutiques":
        for i in range(0, int(max_results)):
            mock_records.append(MockZenodoRecord(i, "Example Tool %s" % i,
                                                 long_description,
                                                 "exampleTool%s.json" % i, i))
    # Return only records containing the query
    else:
        mock_records.append(MockZenodoRecord(1234567, query))
        if not exact:
            mock_records.append(MockZenodoRecord(1234568, "foo-" + query))
            mock_records.append(MockZenodoRecord(1234569, query + "-bar"))

    return mock_zenodo_search(mock_records)


class TestSearch(TestCase):

    @mock.patch('requests.get')
    def test_search_all(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs:\
            mock_get("", False, *args, **kwargs)
        results = bosh(["search"])
        self.assertGreater(len(results), 0)
        self.assertEqual(list(results[0].keys()),
                         ["ID", "TITLE", "DESCRIPTION",
                          "DOWNLOADS"])

    @mock.patch('requests.get')
    def test_search_query(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs:\
            mock_get("Example Tool 5", False, *args, **kwargs)
        results = bosh(["search", "Example Tool 5"])
        self.assertGreater(len(results), 0)
        self.assertIn('Example Tool 5', [d['TITLE'] for d in results])
        self.assertIn('foo-Example Tool 5', [d['TITLE'] for d in results])
        self.assertIn('Example Tool 5-bar', [d['TITLE'] for d in results])

    @mock.patch('requests.get')
    def test_search_exact_match(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs:\
            mock_get("Example Tool 5", True, *args, **kwargs)
        results = bosh(["search", "Example Tool 5", "--exact"])
        self.assertGreater(len(results), 0)
        self.assertIn('Example Tool 5', [d['TITLE'] for d in results])
        self.assertNotIn('foo-Example Tool 5', [d['TITLE'] for d in results])
        self.assertNotIn('Example Tool 5-bar', [d['TITLE'] for d in results])

    @mock.patch('requests.get')
    def test_search_verbose(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs:\
            mock_get("", False, *args, **kwargs)
        results = bosh(["search", "-v"])
        self.assertGreater(len(results), 0)
        self.assertEqual(list(results[0].keys()),
                         ["ID", "TITLE", "DESCRIPTION", "PUBLICATION DATE",
                          "DEPRECATED", "DOWNLOADS", "AUTHOR", "VERSION",
                          "DOI", "SCHEMA VERSION", "CONTAINER", "TAGS"])

    @mock.patch('requests.get')
    def test_search_specify_max_results(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs:\
            mock_get("boutiques", False, *args, **kwargs)
        results = bosh(["search", "-m", "20"])
        self.assertEqual(len(results), 20)

    @mock.patch('requests.get')
    def test_search_sorts_by_num_downloads(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs:\
            mock_get("boutiques", False, *args, **kwargs)
        results = bosh(["search"])
        downloads = []
        for r in results:
            downloads.append(r["DOWNLOADS"])
        self.assertEqual(sorted(downloads, reverse=True), downloads)

    @mock.patch('requests.get')
    def test_search_truncates_long_text(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs:\
            mock_get("boutiques", False, *args, **kwargs)
        results = bosh(["search"])
        for r in results:
            for k, v in r.items():
                self.assertLessEqual(len(str(v)), 43)

    @mock.patch('requests.get')
    def test_search_no_trunc(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs:\
            mock_get("boutiques", False, *args, **kwargs)
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
        self.assertTrue(has_no_trunc)
