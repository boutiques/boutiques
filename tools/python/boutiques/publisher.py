#!/usr/bin/env python

from boutiques.validator import validate_descriptor
from boutiques.logger import raise_error, print_info
import json
import requests
import os


class ZenodoError(Exception):
    pass


class Publisher():

    def __init__(self, descriptor_file_name,
                 verbose, sandbox, no_int,
                 auth_token):
        # Straightforward assignments
        self.verbose = verbose
        self.sandbox = sandbox
        self.descriptor_file_name = descriptor_file_name
        self.no_int = no_int
        self.zenodo_access_token = auth_token

        # Validate and load descriptor
        validate_descriptor(descriptor_file_name)
        self.descriptor = json.loads(open(self.descriptor_file_name).read())

        # Get relevant descriptor propertis
        self.url = self.descriptor.get('url')
        self.tool_doi = self.descriptor.get('tool-doi')
        self.descriptor_url = self.descriptor.get('descriptor-url')

        # Get tool author and check that it's defined
        if self.descriptor.get("author") is None:
            raise_error(ZenodoError, "Tool must have an author to be "
                        "published. Add an 'author' property to your "
                        "descriptor.")
        self.creator = self.descriptor['author']

        # Get descriptor doi and check that it's not defined
        if self.descriptor.get('doi') is not None:
            raise_error(ZenodoError, "Descriptor already has a DOI. Please "
                        "remove it from the descriptor before publishing it "
                        "again. A new DOI will be generated.")

        self.config_file = os.path.join(os.path.expanduser('~'), ".boutiques")

        # Fix Zenodo access token
        if self.zenodo_access_token is None:
            self.zenodo_access_token = self.get_zenodo_access_token()
        self.save_zenodo_access_token()

        # Set Zenodo endpoint
        self.zenodo_endpoint = "https://sandbox.zenodo.org" if\
            self.sandbox else "https://zenodo.org"
        if(self.verbose):
            print_info("Using Zenodo endpoint {0}"
                       .format(self.zenodo_endpoint))

    def get_zenodo_access_token(self):
        json_creds = self.read_credentials()
        if json_creds.get(self.config_token_property_name()):
            return json_creds.get(self.config_token_property_name())
        if(self.no_int):
            raise_error(ZenodoError, "Cannot find Zenodo credentials.")
        prompt = ("Please enter your Zenodo access token (it will be "
                  "saved in {0} for future use): ".format(self.config_file))
        try:
            return raw_input(prompt)  # Python 2
        except NameError:
            return input(prompt)  # Python 3

    def save_zenodo_access_token(self):
        json_creds = self.read_credentials()
        json_creds[self.config_token_property_name()] = self.zenodo_access_token
        with open(self.config_file, 'w') as f:
            f.write(json.dumps(json_creds, indent=4, sort_keys=True))
        if(self.verbose):
            print_info("Zenodo access token saved in {0}".
                       format(self.config_file))

    def config_token_property_name(self):
        if self.sandbox:
            return "zenodo-access-token-test"
        return "zenodo-access-token"

    def read_credentials(self):
        try:
            with open(self.config_file, "r") as f:
                json_creds = json.load(f)
        except IOError:
            json_creds = {}
        except ValueError:
            json_creds = {}
        return json_creds

    def zenodo_test_api(self):
        r = requests.get(self.zenodo_endpoint+'/api/deposit/depositions')
        if(r.status_code != 401):
            raise_error(ZenodoError, "Cannot access Zenodo", r)
        if(self.verbose):
            print_info("Zenodo is accessible", r)
        r = requests.get(self.zenodo_endpoint+'/api/deposit/depositions',
                         params={'access_token': self.zenodo_access_token})
        message = "Cannot authenticate to Zenodo API, check you access token"
        if(r.status_code != 200):
            raise_error(ZenodoError, "Cannot authenticate to Zenodo", r)
        if(self.verbose):
            print_info("Authentication to Zenodo successful", r)

    def zenodo_deposit(self):
        headers = {"Content-Type": "application/json"}
        data = self.create_metadata()

        r = requests.post(self.zenodo_endpoint+'/api/deposit/depositions',
                          params={'access_token': self.zenodo_access_token},
                          json={},
                          data=json.dumps(data),
                          headers=headers)
        if(r.status_code != 201):
            raise_error(ZenodoError, "Deposition failed", r)
        zid = r.json()['id']
        if(self.verbose):
            print_info("Deposition succeeded, id is {0}".
                       format(zid), r)
        return zid

    def zenodo_deposit_updated_version(self, deposition_id):
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/actions/newversion'
                          % deposition_id,
                          params={'access_token': self.zenodo_access_token})
        if(r.status_code != 201):
            raise_error(ZenodoError, "Deposition of new version failed", r)
        if(self.verbose):
            print_info("Deposition of new version succeeded", r)
        new_url = r.json()['links']['latest_draft']
        new_zid = new_url.split("/")[-1]
        self.zenodo_update_metadata(new_zid)
        self.zenodo_delete_files(new_zid, r.json()["files"])
        return new_zid

    def zenodo_upload_descriptor(self, deposition_id):
        data = {'filename': os.path.basename(self.descriptor_file_name)}
        files = {'file': open(self.descriptor_file_name, 'rb')}
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/files'
                          % deposition_id,
                          params={'access_token': self.zenodo_access_token},
                          data=data,
                          files=files)
        # Status code is inconsistent with Zenodo documentation

        if(r.status_code != 201):
            raise_error(ZenodoError, "Cannot upload descriptor", r)
        if(self.verbose):
            print_info("Descriptor uploaded to Zenodo", r)

    def zenodo_publish(self, deposition_id):
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/actions/publish'
                          % deposition_id,
                          params={'access_token': self.zenodo_access_token})
        if(r.status_code != 202):
            raise_error(ZenodoError, "Cannot publish descriptor", r)
        if(self.verbose):
            print_info("Descriptor published to Zenodo, doi is {0}".
                       format(r.json()['doi']), r)
        return r.json()['doi']

    def zenodo_update_metadata(self, deposition_id):
        data = self.create_metadata()
        headers = {"Content-Type": "application/json"}
        r = requests.put(self.zenodo_endpoint+'/api/deposit/depositions/%s'
                         % deposition_id,
                         params={'access_token': self.zenodo_access_token},
                         data=json.dumps(data),
                         headers=headers)
        if(r.status_code != 200):
            raise_error(ZenodoError, "Cannot update metadata of new version", r)
        if(self.verbose):
            print_info("Updated metadata of new version", r)

    def zenodo_delete_files(self, deposition_id, files):
        for file in files:
            file_id = file["id"]
            r = requests.delete(self.zenodo_endpoint +
                                '/api/deposit/depositions/%s/files/%s'
                                % (deposition_id, file_id),
                                params={'access_token':
                                        self.zenodo_access_token})
            if(r.status_code != 204):
                raise_error(ZenodoError, "Could not delete file", r)
            if(self.verbose):
                print_info("Deleted file", r)

    def publish(self):
        if(not self.no_int):
            prompt = ("The descriptor will be published to Zenodo, "
                      "this cannot be undone. Are you sure? (Y/n) ")
            try:
                ret = raw_input(prompt)  # Python 2
            except NameError:
                ret = input(prompt)  # Python 3
            if ret.upper() != "Y":
                return
        self.zenodo_test_api()

        # perform a search to check if descriptor is an updated version
        # of an existing one
        from boutiques.searcher import Searcher
        searcher = Searcher(self.descriptor.get("name"), self.verbose,
                            self.sandbox, None)
        r = searcher.zenodo_search()

        id_to_update = 0
        publish_update = False
        for hit in r.json()["hits"]["hits"]:
            title = hit["metadata"]["title"]
            if title == self.descriptor.get("name"):
                id_to_update = hit["id"]
                break

        if id_to_update:
            if(not self.no_int):
                prompt = ("Found an existing record with the same name, "
                          "would you like to update it? "
                          "(Y:Update existing / n:Publish new entry with "
                          "name {}) ".format(self.descriptor.get("name")))
                try:
                    ret = raw_input(prompt)  # Python 2
                except NameError:
                    ret = input(prompt)  # Python 3
                if ret.upper() == "Y":
                    publish_update = True
            else:
                publish_update = True

        if publish_update:
            self.publish_updated_version(id_to_update)
        else:
            self.publish_new_entry()

    def publish_new_entry(self):
        deposition_id = self.zenodo_deposit()
        self.zenodo_upload_descriptor(deposition_id)
        self.doi = self.zenodo_publish(deposition_id)
        self.descriptor['doi'] = self.doi
        with open(self.descriptor_file_name, "w") as f:
                f.write(json.dumps(self.descriptor, indent=4, sort_keys=True))

    def publish_updated_version(self, deposition_id):
        new_deposition_id = self.zenodo_deposit_updated_version(deposition_id)
        self.zenodo_upload_descriptor(new_deposition_id)
        self.doi = self.zenodo_publish(new_deposition_id)
        self.descriptor['doi'] = self.doi
        with open(self.descriptor_file_name, "w") as f:
                f.write(json.dumps(self.descriptor, indent=4, sort_keys=True))

    def create_metadata(self):
        data = {
            'metadata': {
                'title': self.descriptor['name'],
                'upload_type': 'software',
                'description': self.descriptor['description'] or "Boutiques "
                               "descriptor for {0}".format(
                                                   self.descriptor['name']),
                'creators': [{'name': self.creator}],
                'version': self.descriptor['tool-version'],
                'keywords': ['Boutiques',
                             'schema-version:{0}'.
                             format(self.descriptor['schema-version'])]
            }
        }
        keywords = data['metadata']['keywords']
        if self.descriptor.get('tags'):
            for key, value in self.descriptor.get('tags').items():
                # Check if value is a string or a list of strings
                if self.is_str(value):
                    keywords.append(key + ":" + value)
                else:
                    keywords += [key + ":" + item for item in value]
        if self.descriptor.get('container-image'):
            keywords.append(self.descriptor['container-image']['type'])
        if self.url is not None:
            if data['metadata'].get('related_identifiers') is None:
                data['metadata']['related_identifiers'] = []
            data['metadata']['related_identifiers'].append({
                'identifier': self.url,
                'relation': 'hasPart'
            })
        if self.tool_doi is not None:
            if data['metadata'].get('related_identifiers') is None:
                data['metadata']['related_identifiers'] = []
            data['metadata']['related_identifiers'].append({
                'identifier': self.tool_doi,
                'relation': 'hasPart'
            })
        if self.descriptor_url is not None:
            if data['metadata'].get('related_identifiers') is None:
                data['metadata']['related_identifiers'] = []
            data['metadata']['related_identifiers'].append({
                'identifier': self.descriptor_url,
                'relation': 'hasPart'
            })
        return data

    # checks if value is a string
    # try/except is needed for Python2/3 compatibility
    def is_str(self, value):
        try:
            basestring
        except NameError:
            return isinstance(value, str)
        return isinstance(value, basestring)
