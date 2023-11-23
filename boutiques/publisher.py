#!/usr/bin/env python

from boutiques.validator import validate_descriptor, ValidationError
from boutiques.logger import raise_error, print_info
from boutiques.zenodoHelper import ZenodoError, ZenodoHelper
from boutiques.util.utils import customSortDescriptorByKey, loadJson
import simplejson as json
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
        self.descriptor = loadJson(self.descriptor_file_name)

        # remove zenodo prefix of ID to update
        try:
            self.id_to_update = id.split(".", 1)[1] if id else None
        except IndexError:
            raise_error(ZenodoError, "Zenodo ID must be prefixed by "
                                     "'zenodo', e.g. zenodo.123456")

        # Validate and load descriptor
        validate_descriptor(self.descriptor)

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

        # Get tool container and check that it's defined
        if self.descriptor.get("container-image") is None:
            raise_error(ZenodoError, "Tool must have a container image to be "
                        "published. Add a 'container-image' property to your "
                        "descriptor.")

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

    def publish(self):
        if(not self.no_int):
            prompt = ("The descriptor will be published to Zenodo, "
                      "this cannot be undone. Are you sure? (Y/n) ")
            ret = input(prompt)
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
            r = self.zenodo_helper.zenodo_search(searcher.query,
                                                 searcher.query_line)

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
                    ret = input(prompt)
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

        # If in replace mode, remove the old DOI
        if self.descriptor.get('doi'):
            del self.descriptor['doi']
        with open(self.descriptor_file_name, 'w') as fhandle:
            fhandle.write(json.dumps(self.descriptor, indent=4))

        self.zenodo_helper.zenodo_upload_file(
            deposition_id, self.descriptor_file_name,
            zenodo_access_token=self.zenodo_access_token,
            error_msg="Cannot upload descriptor to Zenodo",
            verbose_msg="Descriptor uploaded to Zenodo")
        self.doi = self.zenodo_helper.zenodo_publish(
            self.zenodo_access_token, deposition_id, "Descriptor")

        # Assign new doi to published descriptor
        self.descriptor['doi'] = self.doi
        with open(self.descriptor_file_name, "w") as fhandle:
            fhandle.write(json.dumps(self.descriptor, indent=4))

        if os.path.isfile(self.descriptor_file_name):
            return "OK"
        return False

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
                if isinstance(value, str):
                    keywords.append(key + ":" + value)
                # Tag is of form 'tag-name': ['value1', 'value2'], it is a
                # list of key-value pairs
                elif isinstance(value, list):
                    keywords += [key + ":" + item for item in value]
        if self.descriptor.get('container-image'):
            keywords.append(self.descriptor['container-image']['type'])
        if self.descriptor.get('tests'):
            keywords.append('tested')
        if self.descriptor.get('deprecated-by-doi'):
            keywords.append('deprecated')
            if isinstance(self.descriptor['deprecated-by-doi'], str):
                keywords.append('deprecated-by-doi:' +
                                self.descriptor['deprecated-by-doi'])
            self.addRelatedIdentifiers(
                data, self.descriptor['deprecated-by-doi'],
                'isPreviousVersionOf')

        if self.url is not None:
            self.addRelatedIdentifiers(data, self.url, 'hasPart')
        if self.online_platforms is not None:
            for p in self.online_platforms:
                self.addRelatedIdentifiers(data, p, 'hasPart')
        if self.tool_doi is not None:
            self.addRelatedIdentifiers(data, self.tool_doi, 'hasPart')
        if self.descriptor_url is not None:
            self.addRelatedIdentifiers(data, self.descriptor_url, 'hasPart')
        return data

    def addRelatedIdentifiers(self, data, identifier, relation):
        if data['metadata'].get('related_identifiers') is None:
            data['metadata']['related_identifiers'] = []
        data['metadata']['related_identifiers'].append({
            'identifier': identifier,
            'relation': relation
        })
