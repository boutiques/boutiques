#!/usr/bin/env python

from boutiques.validator import validate_descriptor, ValidationError
from boutiques.logger import raise_error, print_info
from boutiques.zenodoHelper import ZenodoError, ZenodoHelper
import simplejson as json
import requests
import os


class Publisher():

    def __init__(self, descriptor_file_name, auth_token,
                 verbose=False, sandbox=False, no_int=False,
                 replace=False, id=None):
        # Straightforward assignments
        self.verbose = verbose
        self.sandbox = sandbox
        self.descriptor_file_name = descriptor_file_name
        self.no_int = no_int
        self.zenodo_access_token = auth_token
        self.zenodo_helper = ZenodoHelper(sandbox, no_int, verbose)

        # remove zenodo prefix of ID to update
        try:
            self.id_to_update = id.split(".", 1)[1] if id else None
        except IndexError:
            raise_error(ZenodoError, "Zenodo ID must be prefixed by "
                                     "'zenodo', e.g. zenodo.123456")

        # Validate and load descriptor
        validate_descriptor(descriptor_file_name)
        self.descriptor = json.loads(open(self.descriptor_file_name).read())

        # Get relevant descriptor properties
        self.url = self.descriptor.get('url')
        self.tool_doi = self.descriptor.get('tool-doi')
        self.descriptor_url = self.descriptor.get('descriptor-url')
        self.online_platforms = self.descriptor.get('online-platform-urls')

        # Get tool author and check that it's defined
        if self.descriptor.get("author") is None:
            raise_error(ZenodoError, "Tool must have an author to be "
                        "published. Add an 'author' property to your "
                        "descriptor.")
        self.creator = self.descriptor['author']

        # If in replace mode, make sure descriptor has a DOI and get the ID.
        # Otherwise, make sure the descriptor does not have a DOI.
        if replace:
            if self.descriptor.get('doi') is None:
                raise_error(ZenodoError, "To publish an updated version of a "
                            "previously published descriptor, the descriptor "
                            "must contain a DOI. This DOI will be replaced "
                            "with a new one.")
            else:
                self.id_to_update = self.descriptor.get('doi').split(".")[-1]
        elif self.descriptor.get('doi') is not None:
            raise_error(ZenodoError, "Descriptor already has a DOI. Please "
                        "remove it from the descriptor before publishing it "
                        "again, or use the --replace flag to publish an "
                        "updated version. A new DOI will be generated.")

        self.config_file = os.path.join(os.path.expanduser('~'), ".boutiques")

        # Fix Zenodo access token
        self.zenodo_access_token = self.zenodo_helper \
            .verify_zenodo_access_token(self.zenodo_access_token)

        # Set Zenodo endpoint
        self.zenodo_endpoint = self.zenodo_helper.get_zenodo_endpoint()

    def zenodo_upload_descriptor(self, deposition_id):
        # If in replace mode, remove the old DOI
        if self.descriptor.get('doi'):
            del self.descriptor['doi']

        with open(self.descriptor_file_name, 'w') as fhandle:
            fhandle.write(json.dumps(self.descriptor, indent=4))

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

        if self.id_to_update is not None:
            publish_update = True
        else:
            # perform a search to check if descriptor is an updated version
            # of an existing one
            from boutiques.searcher import Searcher
            searcher = Searcher(self.descriptor.get("name"), self.verbose,
                                self.sandbox, exact_match=True)
            r = searcher.zenodo_search()

            publish_update = False
            for hit in r.json()["hits"]["hits"]:
                title = hit["metadata"]["title"]
                if title == self.descriptor.get("name"):
                    self.id_to_update = hit["id"]
                    break

            if self.id_to_update is not None:
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
            deposition_id = self.zenodo_helper.zenodo_deposit_updated_version(
                self.create_metadata(), self.zenodo_access_token,
                self.id_to_update)
        else:
            deposition_id = self.zenodo_helper.zenodo_deposit(
                self.create_metadata(), self.zenodo_access_token)

        self.zenodo_upload_descriptor(deposition_id)
        self.doi = self.zenodo_helper.zenodo_publish(
            self.zenodo_access_token, deposition_id, "Descriptor")
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
                # Tag is of form 'tag-name': true, it is a single-string
                if isinstance(value, bool):
                    keywords.append(key)
                # Tag is of form 'tag-name':'tag-value', it is a key-value pair
                if self.is_str(value):
                    keywords.append(key + ":" + value)
                # Tag is of form 'tag-name': ['value1', 'value2'], it is a
                # list of key-value pairs
                elif isinstance(value, list):
                    keywords += [key + ":" + item for item in value]
        if self.descriptor.get('container-image'):
            keywords.append(self.descriptor['container-image']['type'])
        if self.descriptor.get('tests'):
            keywords.append('tested')
        if self.url is not None:
            self.addHasPart(data, self.url)
        if self.online_platforms is not None:
            for p in self.online_platforms:
                self.addHasPart(data, p)
        if self.tool_doi is not None:
            self.addHasPart(data, self.tool_doi)
        if self.descriptor_url is not None:
            self.addHasPart(data, self.descriptor_url)
        return data

    # Check if value is a string
    # try/except is needed for Python2/3 compatibility
    def is_str(self, value):
        try:
            basestring
        except NameError:
            return isinstance(value, str)
        return isinstance(value, basestring)

    def addHasPart(self, data, identifier):
        if data['metadata'].get('related_identifiers') is None:
            data['metadata']['related_identifiers'] = []
        data['metadata']['related_identifiers'].append({
            'identifier': identifier,
            'relation': 'hasPart'
        })
