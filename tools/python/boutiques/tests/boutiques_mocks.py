import os
from boutiques import __file__ as bfile


class MockHttpResponse:
    def __init__(self, status_code, mock_json={}):
        self.status_code = status_code
        self.mock_json = mock_json

    def json(self):
        return self.mock_json


class MockZenodoRecord:
    def __init__(self, id, title, description="", filename="", downloads=1,
                 keywords=[], is_last_version=True):
        self.id = id
        self.title = title
        self.filename = filename
        self.downloads = downloads
        self.description = description
        self.keywords = keywords
        self.is_last_version = is_last_version


# Mock object representing the current version of Example Boutiques Tool
# on Zenodo
example_boutiques_tool = MockZenodoRecord(2644621, "Example Boutiques Tool",
                                          "", "https://zenodo.org/api/files/"
                                          "009cc264-76f6-459c-a824-"
                                          "5db6241a979f/example1_docker.json")


def mock_zenodo_test_api():
    return MockHttpResponse(200)


def mock_zenodo_update_metadata():
    return MockHttpResponse(200)


def mock_put(*args, **kwargs):
    return MockHttpResponse(200)


def mock_zenodo_search(mock_records):
    mock_results = []
    for record in mock_records:
        mock_results.append(get_zenodo_record(record))
    mock_json = {"hits": {"hits": mock_results, "total": len(mock_results)}}
    return MockHttpResponse(200, mock_json)


def mock_zenodo_upload_descriptor():
    return MockHttpResponse(201)


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


def mock_zenodo_publish(mock_zid):
    mock_json = {"doi": "10.5281/zenodo.%s" % mock_zid}
    return MockHttpResponse(202, mock_json)


def mock_zenodo_delete_files():
    return MockHttpResponse(204)


def mock_delete(*args, **kwargs):
    return MockHttpResponse(204)


def mock_zenodo_test_api_fail():
    return MockHttpResponse(401)


def mock_zenodo_no_permission():
    return MockHttpResponse(403)


def mock_get_invalid_nexus_endpoint():
    return "https://invalid.nexus.endpoint/v1"


def mock_get_empty_nexus_credentials():
    return {}


def mock_empty_function():
    return


def get_zenodo_record(record):
    return {
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
            "publication_date": "2020-04-15",
            "relations": {
                'version': [
                    {
                        'count': 4,
                        'index': 3,
                        'is_last': record.is_last_version,
                        'last_child': {'pid_value': '33333'}
                    }
                ]
            },
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


def mock_get_data_cache():
    return os.path.join(os.path.dirname(bfile), "tests", "test-data-cache")


def mock_get_data_cache_file():
    return os.path.join(
        os.path.dirname(bfile), "tests", "test-data-cache", "nexus")


def mock_get_publish_single():
    return ([mock_zenodo_test_api_fail(),
             mock_zenodo_test_api(),
             mock_zenodo_test_api_fail(),
             mock_zenodo_test_api(),
             mock_zenodo_test_api_fail(),
             mock_zenodo_test_api(),
             mock_zenodo_test_api_fail(),
             mock_zenodo_test_api()])


def mock_post_publish_single():
    return([mock_zenodo_deposit(1234567),
            mock_zenodo_upload_descriptor(),
            mock_zenodo_publish(1234567),
            mock_zenodo_deposit(1234567),
            mock_zenodo_upload_descriptor(),
            mock_zenodo_publish(1234567)])


def mock_get_publish_bulk():
    return ([mock_zenodo_test_api_fail(),
             mock_zenodo_test_api()])


def mock_post_publish_bulk():
    return ([mock_zenodo_deposit(1234567),
             mock_zenodo_upload_descriptor(),
             mock_zenodo_upload_descriptor(),
             mock_zenodo_publish(1234567)])


def mock_get_publish_individual():
    return ([mock_zenodo_test_api_fail(),
             mock_zenodo_test_api()])


def mock_post_publish_individual():
    return ([mock_zenodo_deposit(1234567),
             mock_zenodo_upload_descriptor(),
             mock_zenodo_publish(1234567),
             mock_zenodo_deposit(2345678),
             mock_zenodo_upload_descriptor(),
             mock_zenodo_publish(2345678)])


def mock_get(*args, **kwargs):
    # Check that URL looks good
    split = args[0].split('/')
    assert(len(split) >= 5)

    command = split[4]
    # Records command
    if command == "records":
        assert(len(split) >= 6)
        record_id = split[10] if len(split) > 6 else split[5]
        if record_id == "00000":
            # Inexistent tool
            return MockHttpResponse(404)
        mock_record1 = example_boutiques_tool
        mock_record1.id = int(record_id)
        if record_id == "22222":
            mock_record1.is_last_version = False
        mock_get = get_zenodo_record(mock_record1)
        if "?q=keywords:" in args[0]:
            return mock_zenodo_search([mock_record1])
        return MockHttpResponse(200, mock_get)

    # Deposit command
    if command == "deposit":
        # Check auth
        if kwargs.get('params') and kwargs.get('params').get('access_token'):
            return MockHttpResponse(200)
        else:
            return MockHttpResponse(401)


def mock_post(*args, **kwargs):
    # Check that URL looks good
    split = args[0].split('/')
    assert(len(split) >= 5)
    command = split[4]
    # Deposit command
    if command == "deposit":
        json = {"links": {"latest_draft": "plop/coin/pan/12345"},
                "doi": "foo/bar", "files": [{"id": "qwerty"}]}
        if args[0].endswith("actions/publish"):
            return MockHttpResponse(202, json)
        else:
            return MockHttpResponse(201, json)


def mock_download_deprecated(url, file_path):
    # Mocks the download and save of a deprecated descriptor
    example_1_path = os.path.join(
                        os.path.join(
                            os.path.dirname(bfile), "schema", "examples",
                            "example1", "example1_docker.json"))
    example_1_json = loadJson(example_1_path)
    example_1_json['deprecated-by-doi'] = "a_doi"
    cache_dir = os.path.join(os.path.expanduser('~'), ".cache",
                             "boutiques", "production")
    with open(file_path, 'w') as f:
        f.write(json.dumps(example_1_json))
    return [f.name]
