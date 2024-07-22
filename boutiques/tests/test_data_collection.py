import datetime as dt
import glob
import os
import subprocess

import mock
import pytest
from boutiques_mocks import example_boutiques_tool, mock_get

import boutiques as bosh
from boutiques import __file__ as bfile
from boutiques.localExec import loadJson
from boutiques.tests.BaseTest import BaseTest


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
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("data_collection")

    @pytest.fixture(autouse=True)
    def clean_up(self):
        yield
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
        invoc = os.path.join(os.path.dirname(bfile), "schema",
                             "examples", "example1", "invocation.json")
        bosh.execute("launch",
                     self.example1_descriptor,
                     invoc,
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

        invoc = os.path.join(os.path.dirname(bfile), "schema",
                             "examples", "example1", "invocation.json")
        bosh.execute("launch",
                     self.example1_descriptor,
                     invoc,
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

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    @mock.patch('requests.get', return_value=mock_get())
    def test_read_doi_zenodo(self, mock_get):
        invoc = os.path.join(os.path.dirname(bfile), "schema",
                             "examples", "example1", "invocation.json")
        bosh.execute("launch", "zenodo." + str(example_boutiques_tool.id),
                     invoc)
        data_collect_dict = retrieve_data_record()

        summary = data_collect_dict.get("summary")
        self.assertIsNotNone(summary)
        self.assertEqual(summary.get("descriptor-doi"),
                         "10.5281/zenodo." + str(example_boutiques_tool.id))

    def test_directory_input_output(self):
        import shutil
        if os.path.exists(self.test_temp):
            shutil.rmtree(self.test_temp)
        bosh.execute("launch",
                     self.get_file_path("dir_input.json"),
                     self.get_file_path("dir_invocation.json"),
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

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_add_provenance(self):
        provenance = """{
            \"engine\": \"http://cbrain.ca\",
            \"dataset id\": \"1234\",
            \"cluster\": \"beluga\"
        }"""
        invoc = os.path.join(os.path.dirname(bfile), "schema",
                             "examples", "example1", "invocation.json")
        bosh.execute("launch",
                     self.example1_descriptor,
                     invoc,
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
