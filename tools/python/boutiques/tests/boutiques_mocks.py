class MockHttpResponse:
    def __init__(self, status_code, mock_json={}):
        self.status_code = status_code
        self.mock_json = mock_json

    def json(self):
        return self.mock_json


class MockZenodoRecord:
    def __init__(self, id, title, description="", filename="", downloads=1):
        self.id = id
        self.title = title
        self.filename = filename
        self.downloads = downloads
        self.description = description


# Mock object representing the current version of Example Boutiques Tool
# on Zenodo
example_boutiques_tool = MockZenodoRecord(2634310, "Example Boutiques Tool",
                                          "", "https://zenodo.org/api/files/"
                                          "009cc264-76f6-459c-a824-"
                                          "5db6241a979f/example1_docker.json")


def mock_zenodo_test_api():
    return MockHttpResponse(200)


def mock_zenodo_test_api_fail():
    return MockHttpResponse(401)


def mock_zenodo_deposit(mock_zid):
    mock_json = {"id": mock_zid}
    return MockHttpResponse(201, mock_json)


def mock_zenodo_deposit_updated(old_zid, new_zid):
    mock_json = {
                  "links": {
                    "latest_draft": "https://zenodo.org/api/record/%s"
                                    % new_zid
                  },
                  "files": [
                    {
                      "id": 1234
                    }
                  ],
                  "doi": "10.5072/zenodo.%s"
                         % old_zid
                }
    return MockHttpResponse(201, mock_json)


def mock_zenodo_upload_descriptor():
    return MockHttpResponse(201)


def mock_zenodo_publish(mock_zid):
    mock_json = {"doi": "10.5281/zenodo.%s" % mock_zid}
    return MockHttpResponse(202, mock_json)


def mock_zenodo_update_metadata():
    return MockHttpResponse(200)


def mock_zenodo_delete_files():
    return MockHttpResponse(204)


def mock_zenodo_search(mock_records):
    mock_results = []
    for record in mock_records:
        mock_result = {
                        "doi": "10.5281/zenodo.%s" % record.id,
                        "files": [
                          {
                            "links": {
                              "self": record.filename
                            }
                          }
                        ],
                        "id": record.id,
                        "metadata": {
                          "creators": [
                            {
                              "name": "Test author"
                            }
                          ],
                          "description": record.description,
                          "doi": "10.5281/zenodo.%s" % record.id,
                          "keywords": [
                            "schema-version:0.5",
                            "docker"
                          ],
                          "title": record.title,
                          "version": "0.0.1"
                        },
                        "stats": {
                          "version_downloads": record.downloads
                        }
                      }
        mock_results.append(mock_result)
    mock_json = {"hits": {"hits": mock_results, "total": len(mock_results)}}
    return MockHttpResponse(200, mock_json)


def mock_zenodo_no_permission():
    return MockHttpResponse(403)
