from unittest import TestCase
import datetime as dt
import os
import glob
import mock
from boutiques import __file__ as bfile
from boutiques.localExec import loadJson
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord
import boutiques as bosh

def mock_get():
    mock_record = MockZenodoRecord(1472823, "Example Boutiques Tool", "",
                                   "https://zenodo.org/api/files/"
                                   "e5628764-fc57-462e-9982-65f8d6fdb487/"
                                   "example1_docker.json")
    return mock_zenodo_search([mock_record])

def retrieve_data_record():
    data_collect_dict = {}
    cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques", "data")
    if os.path.exists(cache_dir):
        cache_fls = glob.glob(cache_dir + "/*")
        if cache_fls:
            latest_file = max(cache_fls, key=os.path.getctime)
            path = os.path.join(cache_dir, latest_file)
            data_collect_dict = loadJson(path)
    return data_collect_dict

class TestDataCollection(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def clean_up(self):
        # Clean up data collection files
        cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques", "data")
        if os.path.exists(cache_dir):
            cache_fls = os.listdir(cache_dir)
            for fl in cache_fls:
                path = os.path.join(cache_dir, fl)
                st = os.stat(path)
                mtime = dt.datetime.fromtimestamp(st.st_mtime)
                if mtime > dt.datetime.now() - dt.timedelta(minutes=2):
                    os.remove(path)

    def test_data_collection(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        bosh.execute("launch",
                        os.path.join(example1_dir,
                                    "example1_docker.json"),
                        os.path.join(example1_dir,
                                    "invocation.json"))
        data_collect_dict = retrieve_data_record()

        assert data_collect_dict.get("summary") is not None
        summary = data_collect_dict.get("summary")
        assert summary.get("name") == "Example Boutiques Tool"
        assert data_collect_dict.get("public-invocation") is not None
        public_in = data_collect_dict.get("public-invocation")
        assert public_in.get("config_num") == 4
        assert public_in.get("enum_input") == "val1"
        assert public_in.get("file_input") is not None
        file_input = public_in.get("file_input")
        assert file_input.get("file-name") == "setup.py"
        assert file_input.get("hash") is not None
        assert data_collect_dict.get("public-output") is not None
        public_out = data_collect_dict.get("public-output")
        assert public_out.get("stdout") == "This is stdout"
        assert public_out.get("stderr") == "This is stderr"
        assert public_out.get("exit-code") == 0
        assert public_out.get("error-message") == ""
        assert public_out.get("output-files") is not None
        output_files = public_out.get("output-files")
        assert output_files.get("logfile") is not None
        assert output_files.get("config_file") is not None
        logfile = output_files.get("logfile")
        assert logfile.get("file-name") == "log-4-coin;plop.txt"

        self.clean_up()

    def test_skip_collection(self):
        # Register original size of cache directory for comparison
        cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques", "data")
        original_size = 0
        if os.path.exists(cache_dir):
            cache_fls = os.listdir(cache_dir)
            original_size = len(cache_fls)

        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        bosh.execute("launch",
                        os.path.join(example1_dir,
                                    "example1_docker.json"),
                       os.path.join(example1_dir,
                                    "invocation.json"),
                       "--skip-data-collection")

        new_size = 0
        if os.path.exists(cache_dir):
            cache_fls = os.listdir(cache_dir)
            new_size = len(cache_fls)
        assert new_size == original_size

        self.clean_up()

    @mock.patch('requests.get', return_value=mock_get())
    def test_read_doi_zenodo(self, mock_get):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        bosh.execute("launch", "zenodo.1472823",
                        os.path.join(example1_dir,
                                    "invocation.json"))
        data_collect_dict = retrieve_data_record()

        assert data_collect_dict.get("summary") is not None
        summary = data_collect_dict.get("summary")
        assert summary.get("descriptor-doi") == "zenodo.1472823"

        self.clean_up()

    def test_directory_input_output(self):
        example1_dir = self.get_examples_dir()
        bosh.execute("launch",
                    os.path.join(example1_dir,
                                 "dir_input.json"),
                    os.path.join(example1_dir,
                                 "dir_invocation.json"))
        data_collect_dict = retrieve_data_record()

        assert data_collect_dict.get("public-invocation") is not None
        public_in = data_collect_dict.get("public-invocation")
        assert public_in.get("input_dir") is not None
        input_dir = public_in.get("input_dir")
        assert input_dir.get("files") is not None
        files = input_dir.get("files")
        assert len(files) == 3

        assert data_collect_dict.get("public-output") is not None
        public_out = data_collect_dict.get("public-output")
        assert public_out.get("output-files") is not None
        output_files = public_out.get("output-files")
        assert output_files.get("results")
        results = output_files.get("results")
        assert results.get("files")
        files = results.get("files")
        assert len(files) == 3

        self.clean_up()
