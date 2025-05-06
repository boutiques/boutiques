import os

from boutiques import __file__ as bfile


class MockHttpResponse:
    def __init__(self, status_code, mock_json={}):
        self.status_code = status_code
        self.mock_json = mock_json

    def json(self):
        return self.mock_json


ZENODO_RECORD = 129904
ZENODO_FILE = (
    f"https://sandbox.zenodo.org/records/{ZENODO_RECORD}/files/example1_docker.json"
)


class MockZenodoRecord:
    def __init__(
        self,
        id,
        title,
        description="",
        filename="",
        downloads=1,
        keywords=[],
        is_last_version=True,
    ):
        self.id = id
        self.title = title
        self.filename = filename
        self.downloads = downloads
        self.description = description
        self.keywords = keywords
        self.is_last_version = is_last_version

    def reset(
        self,
        id=ZENODO_RECORD,
        title="Example Boutiques Tool",
        description="",
        filename=ZENODO_FILE,
        downloads=1,
        keywords=[],
        is_last_version=True,
    ):
        self.id = id
        self.title = title
        self.filename = filename
        self.downloads = downloads
        self.description = description
        self.keywords = keywords
        self.is_last_version = is_last_version


# Mock object representing the current version of Example Boutiques Tool
# on Zenodo
example_boutiques_tool = MockZenodoRecord(
    ZENODO_RECORD,
    "Example Boutiques Tool",
    filename=ZENODO_FILE,
)


def mock_get():
    return mock_zenodo_search(
        [
            MockZenodoRecord(
                ZENODO_RECORD,
                "Example Boutiques Tool",
                filename=ZENODO_FILE,
            )
        ]
    )


def mock_zenodo_test_api(*args, **kwargs):
    return MockHttpResponse(200)


def mock_zenodo_upload_descriptor():
    return MockHttpResponse(201)


def mock_zenodo_deposit(mock_zid):
    mock_json = {"id": mock_zid}
    return MockHttpResponse(201, mock_json)


def mock_zenodo_publish(mock_zid):
    mock_json = {"doi": f"10.5281/zenodo.{mock_zid}"}
    return MockHttpResponse(202, mock_json)


def mock_zenodo_delete_files(*args, **kwargs):
    return MockHttpResponse(204)


def mock_zenodo_test_api_fail():
    return MockHttpResponse(403)


def mock_zenodo_no_permission():
    return MockHttpResponse(403)


def mock_get_invalid_nexus_endpoint():
    return "https://invalid.nexus.endpoint/v1"


def mock_get_empty_nexus_credentials():
    return {}


def mock_empty_function():
    return


def get_zenodo_record(record, include_version=True):
    record = {
        "doi": f"10.5281/zenodo.{record.id}",
        "files": [{"links": {"self": record.filename}}],
        "id": record.id,
        "metadata": {
            "creators": [{"name": "Test author"}],
            "description": record.description,
            "publication_date": "2020-04-15",
            "relations": {
                "version": [
                    {
                        "count": 4,
                        "index": 3,
                        "is_last": record.is_last_version,
                        "last_child": {"pid_value": "33333"},
                    }
                ]
            },
            "doi": f"10.5281/zenodo.{record.id}",
            "keywords": ["schema-version:0.5", "docker"],
            "title": record.title,
            "version": "0.0.1",
        },
        "stats": {"version_downloads": record.downloads},
    }
    if not include_version:
        del record["metadata"]["version"]
    return record


def mock_get_data_cache():
    return os.path.join(
        os.path.split(os.path.split(bfile)[0])[0],
        "test_temp",
        "test-data-cache",
    )


def mock_zenodo_search(mock_records, include_version=True):
    mock_results = []
    for record in mock_records:
        mock_results.append(get_zenodo_record(record, include_version))
    mock_json = {"hits": {"hits": mock_results, "total": len(mock_results)}}
    return MockHttpResponse(200, mock_json)


def mock_get_data_cache_file():
    return os.path.join(
        os.path.split(os.path.split(bfile)[0])[0],
        "test_temp",
        "test-data-cache",
        "nexus",
    )


def mock_get_publish_single():
    return [
        mock_zenodo_test_api_fail(),
        mock_zenodo_test_api(),
        mock_zenodo_test_api_fail(),
        mock_zenodo_test_api(),
        mock_zenodo_test_api_fail(),
        mock_zenodo_test_api(),
        mock_zenodo_test_api_fail(),
        mock_zenodo_test_api(),
    ]


def mock_post_publish_single():
    return [
        mock_zenodo_deposit(1234567),
        mock_zenodo_upload_descriptor(),
        mock_zenodo_publish(1234567),
        mock_zenodo_deposit(1234567),
        mock_zenodo_upload_descriptor(),
        mock_zenodo_publish(1234567),
    ]


def mock_get_publish_bulk():
    return [mock_zenodo_test_api_fail(), mock_zenodo_test_api()]


def mock_post_publish_bulk():
    return [
        mock_zenodo_deposit(1234567),
        mock_zenodo_upload_descriptor(),
        mock_zenodo_upload_descriptor(),
        mock_zenodo_publish(1234567),
    ]
