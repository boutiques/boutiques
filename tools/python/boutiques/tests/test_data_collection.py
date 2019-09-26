from unittest import TestCase
import datetime as dt
import os
import glob
import mock
import subprocess
import pytest
from boutiques import __file__ as bfile
from boutiques.localExec import loadJson
from boutiques.util.BaseTest import BaseTest
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord,\
    example_boutiques_tool
import boutiques as bosh


def mock_get():
    return mock_zenodo_search([example_boutiques_tool])


def retrieve_data_record():
    data_collect_dict = {}
    cache_dir = os.path.join(os.path.expanduser('~'),
                             ".cache", "boutiques", "data")
    if os.path.exists(cache_dir):
        cache_fls = glob.glob(cache_dir + "/*")
        if cache_fls:
            latest_file = max(cache_fls, key=os.path.getctime)
            path = os.path.join(cache_dir, latest_file)
            data_collect_dict = loadJson(path)
    return data_collect_dict


class TestDataCollection(BaseTest):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def clean_up(self):
        # Clean up data collection files
        cache_dir = os.path.join(os.path.expanduser('~'),
                                 ".cache", "boutiques", "data")
        if os.path.exists(cache_dir):
            cache_fls = os.listdir(cache_dir)
            for fl in cache_fls:
                path = os.path.join(cache_dir, fl)
                st = os.stat(path)
                mtime = dt.datetime.fromtimestamp(st.st_mtime)
                if mtime > dt.datetime.now() - dt.timedelta(minutes=2):
                    os.remove(path)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_data_collection(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        bosh.execute("launch",
                     os.path.join(example1_dir,
                                  "example1_docker.json"),
                     os.path.join(example1_dir,
                                  "invocation.json"),
                     "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                     "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))
        data_collect_dict = retrieve_data_record()

        summary = data_collect_dict.get("summary")
        self.assertIsNotNone(summary)
        self.assertEqual(summary.get("name"), "Example Boutiques Tool")
        public_in = data_collect_dict.get("public-invocation")
        self.assertIsNotNone(public_in)
        self.assertEqual(public_in.get("config_num"), 4)
        self.assertEqual(public_in.get("enum_input"), "val1")
        file_input = public_in.get("file_input")
        self.assertIsNotNone(file_input)
        self.assertEqual(file_input.get("file-name"), "setup.py")
        self.assertIsNotNone(file_input.get("md5sum"))
        public_out = data_collect_dict.get("public-output")
        self.assertIsNotNone(public_out)
        self.assertEqual(public_out.get("stdout"), "This is stdout")
        self.assertEqual(public_out.get("stderr"), "This is stderr")
        self.assertEqual(public_out.get("exit-code"), 0)
        self.assertEqual(public_out.get("error-message"), "")
        output_files = public_out.get("output-files")
        self.assertIsNotNone(output_files)
        self.assertIsNotNone(output_files.get("logfile"))
        self.assertIsNotNone(output_files.get("config_file"))
        logfile = output_files.get("logfile")
        self.assertEqual(logfile.get("file-name"), "log-4-coin;plop.txt")

        self.clean_up()

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_skip_collection(self):
        # Register original size of cache directory for comparison
        cache_dir = os.path.join(os.path.expanduser('~'),
                                 ".cache", "boutiques", "data")
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
                     "--skip-data-collection",
                     "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                     "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))

        new_size = 0
        if os.path.exists(cache_dir):
            cache_fls = os.listdir(cache_dir)
            new_size = len(cache_fls)
        self.assertEqual(new_size, original_size)

        self.clean_up()

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    @mock.patch('requests.get', return_value=mock_get())
    def test_read_doi_zenodo(self, mock_get):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        bosh.execute("launch", "zenodo." + str(example_boutiques_tool.id),
                     os.path.join(example1_dir,
                                  "invocation.json"))
        data_collect_dict = retrieve_data_record()

        summary = data_collect_dict.get("summary")
        self.assertIsNotNone(summary)
        self.assertEqual(summary.get("descriptor-doi"),
                         "10.5281/zenodo." + str(example_boutiques_tool.id))
        self.clean_up()

    def test_directory_input_output(self):
        example1_dir = self.get_examples_dir()
        bosh.execute("launch",
                     os.path.join(example1_dir,
                                  "dir_input.json"),
                     os.path.join(example1_dir,
                                  "dir_invocation.json"),
                     "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                     "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))
        data_collect_dict = retrieve_data_record()

        public_in = data_collect_dict.get("public-invocation")
        self.assertIsNotNone(public_in)
        input_dir = public_in.get("input_dir")
        self.assertIsNotNone(input_dir)
        files = input_dir.get("files")
        self.assertIsNotNone(files)
        self.assertEqual(len(files), 2)

        public_out = data_collect_dict.get("public-output")
        self.assertIsNotNone(public_out)
        output_files = public_out.get("output-files")
        self.assertIsNotNone(output_files)
        results = output_files.get("results")
        self.assertIsNotNone(results)
        files = results.get("files")
        self.assertIsNotNone(files)
        self.assertEqual(len(files), 2)

        self.clean_up()

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_add_provenance(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        provenance = """{
            \"engine\": \"http://cbrain.ca\",
            \"dataset id\": \"1234\",
            \"cluster\": \"beluga\"
        }"""
        bosh.execute("launch",
                     os.path.join(example1_dir,
                                  "example1_docker.json"),
                     os.path.join(example1_dir,
                                  "invocation.json"),
                     "-v", "{}:/test_mount1".format(
                        self.get_file_path("example1_mount1")),
                     "-v", "{}:/test_mount2".format(
                        self.get_file_path("example1_mount2")),
                     "--provenance", provenance)
        data_collect_dict = retrieve_data_record()

        summary = data_collect_dict.get("summary")
        self.assertIsNotNone(summary)
        self.assertEqual(summary.get("name"), "Example Boutiques Tool")
        public_in = data_collect_dict.get("public-invocation")
        self.assertIsNotNone(public_in)
        self.assertEqual(public_in.get("config_num"), 4)
        self.assertEqual(public_in.get("enum_input"), "val1")
        file_input = public_in.get("file_input")
        self.assertIsNotNone(file_input)
        self.assertEqual(file_input.get("file-name"), "setup.py")
        self.assertIsNotNone(file_input.get("md5sum"))
        public_out = data_collect_dict.get("public-output")
        self.assertIsNotNone(public_out)
        self.assertEqual(public_out.get("stdout"), "This is stdout")
        self.assertEqual(public_out.get("stderr"), "This is stderr")
        self.assertEqual(public_out.get("exit-code"), 0)
        self.assertEqual(public_out.get("error-message"), "")
        output_files = public_out.get("output-files")
        self.assertIsNotNone(output_files)
        self.assertIsNotNone(output_files.get("logfile"))
        self.assertIsNotNone(output_files.get("config_file"))
        logfile = output_files.get("logfile")
        self.assertEqual(logfile.get("file-name"), "log-4-coin;plop.txt")
        provenance = data_collect_dict.get("additional-information")
        self.assertEqual(provenance.get("engine"), "http://cbrain.ca")
        self.assertEqual(provenance.get("dataset id"), "1234")
        self.assertEqual(provenance.get("cluster"), "beluga")

        self.clean_up()
