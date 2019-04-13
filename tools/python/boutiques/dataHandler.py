#!/usr/bin/env python
import os
import requests
import time
import hashlib
from boutiques.logger import raise_error, print_info
from boutiques.util.utils import extractFileName, loadJson
from boutiques.zenodoHelper import ZenodoHelper, ZenodoError


class DataHandler(object):

    # Constructor
    def __init__(self):
        self.cache_dir = getDataCacheDir()
        self.cache_files = os.listdir(self.cache_dir)
        self.descriptor_files = [fl for fl in self.cache_files
                                 if fl.split('_')[0] == "descriptor"]
        self.record_files = [fl for fl in self.cache_files
                             if fl not in self.descriptor_files]

    # Function to display the contents of the cache
    # Option to display an example file which displays an pre-made example file
    # or the first file of the cache if it exists
    # Otherwise displays information about the cache and a list of files
    def inspect(self, example=False):
        self.example = example
        # Display an example json file
        if self.example:
            # Display the first file in cache
            if len(self.record_files) > 0:
                filename = self.record_files[0]
                file_path = os.path.join(self.cache_dir, filename)
                self._display_file(file_path)
            else:
                print("No records in the cache at the moment.")
        # Print information about files in cache
        else:
            print("There are {} unpublished records in the cache"
                  .format(len(self.record_files)))
            print("There are {} unpublished descriptors in the cache"
                  .format(len(self.descriptor_files)))
            for i in range(len(self.cache_files)):
                print(self.cache_files[i])

    # Private function to print a file to console
    def _display_file(self, file_path):
        with open(file_path, 'r') as file_in:
            print(file_in.read())
            file_in.close()

    # Function to publish a data set to Zenodo
    # Options allow to only publish a single file, publish files individually as
    # data sets or bulk publish all files in the cache as one data set (default)
    def publish(self, file, zenodo_token, author,
                individually=False, sandbox=False, no_int=False,
                verbose=False):
        self.filename = extractFileName(file)
        self.zenodo_access_token = zenodo_token
        self.author = "Anonymous"
        if author is not None:
            self.author = author
        self.individual = individually
        self.sandbox = sandbox
        self.no_int = no_int
        self.verbose = verbose
        self.zenodo_helper = ZenodoHelper(sandbox, no_int, verbose)
        self.zenodo_endpoint = self.zenodo_helper.get_zenodo_endpoint()

        # Fix Zenodo access token
        self.zenodo_access_token = self.zenodo_helper \
            .verify_zenodo_access_token(self.zenodo_access_token)

        # Verify publishing
        if not self.no_int:
            prompt = self._get_publishing_prompt()
            try:
                ret = raw_input(prompt)  # Python 2
            except NameError:
                ret = input(prompt)  # Python 3
            if ret.upper() != "Y":
                return

        # Flag for data-set size
        self.bulk_publish = False
        # Single record publication
        if self.filename is not None:
            self._file_exists_in_cache(self.filename)
            self._zenodo_publish([self.filename])
        # All records published to individual data-sets
        elif individually:
            for file in self.record_files:
                self._zenodo_publish([file])
        # All records published to one data-set
        else:
            self.bulk_publish = True
            self._zenodo_publish(self.record_files)

    # Private method to publish all the records in file_list to a single
    # data-set on Zenodo
    def _zenodo_publish(self, files_list):
        # Filter files_list by records with Zenodo ids
        records_dict = self._checkPulblishable(files_list)
        # Publishable list is empty, end execution
        if len(records_dict) == 0:
            return

        # Create deposition
        deposition_id = self.zenodo_helper.zenodo_deposit(
            self._create_metadata(records_dict), self.zenodo_access_token)

        # Upload all files in files_list to deposition
        for file in records_dict.keys():
            self._zenodo_upload_dataset(deposition_id, file)

        # Publish deposition
        msg_obj = "Records" if self.bulk_publish else "Record"
        doi = self.zenodo_helper.zenodo_publish(self.zenodo_access_token,
                                                deposition_id, msg_obj)
        # Clear cache of published records
        if doi:
            self._clean_cache(records_dict)

    # Private function to filter out records that can not be published
    # because they lack a descriptor doi
    def _checkPulblishable(self, files_list):
        # dict {filename: content_dict}
        desc_to_publish = set()
        publishable_dict = {}
        for fl in files_list:
            fl_path = os.path.join(self.cache_dir, fl)
            fl_dict = loadJson(fl_path)
            doi = fl_dict.get('summary').get('descriptor-doi')
            # Descriptor is not publish, record contains link to file
            if doi.split("_")[0] == "descriptor":
                desc_path = os.path.join(self.cache_dir, doi)
                desc_dict = loadJson(desc_path)
                # Descriptor is published, record needs to be updated
                if desc_dict.get('doi') is not None:
                    fl_dict['summary']['descriptor-doi'] = desc_dict['doi']
                    publishable_dict[fl] = fl_dict
                # Descriptor isn't published, inform user with full prompt
                else:
                    print("Record {0} cannot be published as its descriptor "
                          "is not yet published. ".format(fl))
                    desc_to_publish.add("bosh publish {}".format(desc_path))
            # Descriptor doi is stored correctly in record
            else:
                publishable_dict[fl] = fl_dict
        # Prompt user to publish descriptors
        if len(desc_to_publish) != 0:
            print("Some descriptors have not been published, they can be "
                  "published with following commands:")
            for prompt in desc_to_publish:
                print("\t"+prompt)
        return publishable_dict

    def _create_metadata(self, records_dict):
        url = "https://zenodo.org/record/{}"
        hash = hashlib.md5()
        hash.update(str(time.time()).encode('utf-8'))
        identifier = hash.hexdigest()
        data = {
            'metadata': {
                'title': 'Boutiques-execution-{}'.format(identifier[:6]),
                'upload_type': 'dataset',
                'description': 'Boutiques execution data-set',
                'creators': [{'name': self.author}]
            }
        }
        # Add tool name(s) to keywords
        data['metadata']['keywords'] = [v['summary']['name']
                                        for k, v in records_dict.items()]
        data['metadata']['keywords'].insert(0, 'Boutiques')
        # Add descriptor link(s) to related identifiers
        data['metadata']['related_identifiers'] = \
            [{'identifier': url.format(v['summary']['descriptor-doi']
                                       .split('.')[2]),
             'relation': 'hasPart'} for k, v in records_dict.items()]
        return data

    def _zenodo_upload_dataset(self, deposition_id, file):
        file_path = os.path.join(self.cache_dir, file)
        data = {'filename': file}
        files = {'file': open(file_path, 'rb')}
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/files'
                          % deposition_id,
                          params={'access_token': self.zenodo_access_token},
                          data=data,
                          files=files)

        if(r.status_code != 201):
            raise_error(ZenodoError, "Cannot upload record", r)
        if(self.verbose):
            print_info("Record uploaded to Zenodo", r)

    def _get_publishing_prompt(self):
        if self.filename is not None:
            return ("The dataset {} will be published to Zenodo, "
                    "this cannot be undone. Are you sure? (Y/n) "
                    .format(self.filename))
        if self.individual:
            return ("The records will be published to Zenodo each as "
                    "separate data-sets. This cannont be undone. Are you "
                    "sure? (Y/n ")
        return ("The records will be published to Zenodo as a data-set. This "
                "cannot be undone. Are you sure? (Y/n) ")

    # Private function to remove published files and descriptors which no
    # longer have dependencies
    def _clean_cache(self, records_dict):
        for record in records_dict.keys():
            self.delete(record, True)
        # List remaining records and collect descriptor-doi values
        self.record_files = [fl for fl in os.listdir(self.cache_dir)
                             if fl not in self.descriptor_files]
        doi_list = [loadJson(os.path.join(self.cache_dir, fl))
                    .get('summary').get('descriptor-doi')
                    for fl in self.record_files]

        # Check each descriptor in remaining records
        for descriptor in self.descriptor_files:
            # No records link to descriptor
            if descriptor not in doi_list:
                self.delete(descriptor, True)
                self.descriptor_files.remove(descriptor)

    # Function to remove file(s) from the cache
    # Option all will clear the data collection cache of all files
    # or passing in a file will remove only that file
    # Options are mutually exclusive and one is required
    def delete(self, file=None, no_int=False):
        self.filename = extractFileName(file)
        self.no_int = no_int

        # Verify deletion
        if not self.no_int:
            prompt = self._get_delete_prompt()
            try:
                ret = raw_input(prompt)  # Python 2
            except NameError:
                ret = input(prompt)  # Python 3
            if ret.upper() != "Y":
                return

        # Remove the file specified by the file option
        if file is not None:
            # Check file exists in cache
            self._file_exists_in_cache(file)
            # Remove file from cache
            file_path = os.path.join(self.cache_dir, file)
            os.remove(file_path)
            print_info("File {} has been removed from the data cache"
                       .format(file))
        # Remove all files in the data cache
        else:
            [os.remove(os.path.join(self.cache_dir, f))
             for f in self.cache_files]
            print_info("All files have been removed from the data cache")

    def _file_exists_in_cache(self, filename):
        file_path = os.path.join(self.cache_dir, filename)
        # Incorrect filename input
        if not os.path.isfile(file_path):
            msg = "File {} does not exist in the data cache".format(filename)
            raise_error(ValueError, msg)

    def _get_delete_prompt(self):
        if self.filename is not None:
            return ("The dataset {} will be deleted from the cache, "
                    "this cannot be undone. Are you sure? (Y/n) "
                    .format(self.filename))
        return ("All records will be removed from the cache. This "
                "cannot be undone. Are you sure? (Y/n) ")


def getDataCacheDir():
    cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques")
    data_cache_dir = os.path.join(cache_dir, "data")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    if not os.path.exists(data_cache_dir):
        os.makedirs(data_cache_dir)
    return data_cache_dir
