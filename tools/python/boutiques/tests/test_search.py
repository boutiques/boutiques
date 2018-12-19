from boutiques.bosh import bosh
from unittest import TestCase
import mock
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord


def mock_get(*args, **kwargs):
    query = args[0].split("=")[1]
    query = query[:query.find("&")]
    max_results = args[0].split("=")[-1]

    mock_records = []
    # Return an arbitrary list of results with length max_results
    if query == "boutiques":
        for i in range(0, int(max_results)):
            mock_records.append(MockZenodoRecord(i, "Example Tool %s" % i))
    # Return only the record matching the query
    else:
        mock_records.append(MockZenodoRecord(1234567, query))

    return mock_zenodo_search(mock_records)


class TestSearch(TestCase):

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_all(self, mocked_get):
        results = bosh(["search"])
        assert(len(results) > 0)
        assert(list(results[0].keys()) == ["ID", "TITLE", "DESCRIPTION"])

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_query(self, mock_get):
        results = bosh(["search", "Example Tool 5"])
        assert(len(results) > 0)
        assert("Example Tool 5" in results[0]["TITLE"])

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_verbose(self, mock_get):
        results = bosh(["search", "-v"])
        assert(len(results) > 0)
        assert(list(results[0].keys()) == ["ID", "TITLE", "DESCRIPTION",
                                           "AUTHOR", "VERSION", "DOI",
                                           "SCHEMA VERSION", "CONTAINER",
                                           "TAGS"])

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_specify_max_results(self, mock_get):
        results = bosh(["search", "--sandbox", "-m", "20"])
        assert(len(results) == 20)
