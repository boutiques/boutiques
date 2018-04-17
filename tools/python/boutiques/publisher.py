#!/usr/bin/env python

# Copyright 2015 - 2017:
#   The Royal Institution for the Advancement of Learning McGill University,
#   Centre National de la Recherche Scientifique,
#   University of Southern California,
#   Concordia University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from boutiques.validator import validate_descriptor
import json
import requests
import os


class ZenodoError(Exception):
    pass


class Publisher():

    def __init__(self, descriptor_file_name,
                 creator, affiliation, verbose, sandbox, no_int,
                 auth_token):
        # Straightforward assignments
        self.verbose = verbose
        self.sandbox = sandbox
        self.descriptor_file_name = descriptor_file_name
        self.creator = creator
        self.affiliation = affiliation
        self.no_int = no_int
        self.zenodo_access_token = auth_token

        # Validate and load descriptor
        validate_descriptor(descriptor_file_name)
        self.descriptor = json.loads(open(self.descriptor_file_name).read())

        self.config_file = os.path.join(os.getenv("HOME"), ".boutiques")
        # Fix Zenodo access token
        if self.zenodo_access_token is None:
            self.zenodo_access_token = self.get_zenodo_access_token()
        self.save_zenodo_access_token()

        # Set Zenodo endpoint
        self.zenodo_endpoint = "https://sandbox.zenodo.org" if\
            self.sandbox else "https://zenodo.org"
        if(self.verbose):
            print("[ INFO ] Using Zenodo endpoint {}".
                  format(self.zenodo_endpoint))

    def get_zenodo_access_token(self):
        json_creds = self.read_credentials()
        if json_creds.get(self.config_token_property_name()):
            return json_creds.get(self.config_token_property_name())
        if(self.no_int):
            raise ZenodoError("Cannot find Zenodo credentials.")
        prompt = ("Please enter your Zenodo access token (it will be "
                  "saved in {} for future use): ".format(self.config_file))
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
            print("[ INFO ] Zenodo access token saved in {}".
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
            self.raise_zenodo_error("Cannot access Zenodo", r)
        if(self.verbose):
            self.print_zenodo_info("Zenodo is accessible", r)
        r = requests.get(self.zenodo_endpoint+'/api/deposit/depositions',
                         params={'access_token': self.zenodo_access_token})
        message = "Cannot authenticate to Zenodo API, check you access token"
        if(r.status_code != 200):
            self.raise_zenodo_error("Cannot authenticate to Zenodo", r)
        if(self.verbose):
            self.print_zenodo_info("Authentication to Zenodo successful", r)

    def zenodo_deposit(self):
        headers = {"Content-Type": "application/json"}
        data = {
            'metadata': {
                'title': self.descriptor['name'],
                'upload_type': 'software',
                'description': self.descriptor['description'] or "Boutiques "
                               "descriptor for {}".format(
                                                   self.descriptor['name']),
                'creators': [{'name': self.creator,
                              'affiliation': self.affiliation}],
                'version': self.descriptor['tool-version'],
                'keywords': ['Boutiques',
                             'schema-version:{}'.
                             format(self.descriptor['schema-version'])]
            }
        }
        keywords = data['metadata']['keywords']
        for tag in self.descriptor.get('tags'):
            keywords.append(tag + ":" + self.descriptor['tags'][tag])
        if self.descriptor.get('container-image'):
            keywords.append(self.descriptor['container-image']['type'])

        r = requests.post(self.zenodo_endpoint+'/api/deposit/depositions',
                          params={'access_token': self.zenodo_access_token},
                          json={},
                          data=json.dumps(data),
                          headers=headers)
        if(r.status_code != 201):
            self.raise_zenodo_error("Deposition failed", r)
        zid = r.json()['id']
        if(self.verbose):
            self.print_zenodo_info("Deposition succeeded, id is {}".
                                   format(zid), r)
        return zid

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
            self.raise_zenodo_error("Cannot upload descriptor", r)
        if(self.verbose):
            self.print_zenodo_info("Descriptor uploaded to Zenodo", r)

    def zenodo_publish(self, deposition_id):
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/actions/publish'
                          % deposition_id,
                          params={'access_token': self.zenodo_access_token})
        if(r.status_code != 202):
            self.raise_zenodo_error("Cannot publish descriptor", r)
        if(self.verbose):
            self.print_zenodo_info("Descriptor published to Zenodo, doi is {}"
                                   .format(r.json()['doi']), r)

    def raise_zenodo_error(self, message, r):
        raise ZenodoError("Zenodo error ({0}): {1}."
                          .format(r.status_code, message))

    def print_zenodo_info(self, message, r):
        print("[ INFO ({1}) ] {0}".format(message, r.status_code))

    def publish(self):
        if(not self.no_int):
            prompt = ("The descriptor will be published to Zenodo, "
                      "this cannot be undone. Are you sure? (Y/n) ")
            try:
                ret = raw_input(prompt)  # Python 2
            except NameError:
                ret = input(prompt)  # Python 3
            if ret != "Y":
                return
        self.zenodo_test_api()
        deposition_id = self.zenodo_deposit()
        self.zenodo_upload_descriptor(deposition_id)
        self.zenodo_publish(deposition_id)
