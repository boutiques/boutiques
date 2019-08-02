#!/usr/bin/env python
import os
from builtins import Exception, object, NameError, input, IOError, ValueError
from codecs import open

import simplejson as json
import nexussdk as nexus
from boutiques.logger import raise_error, print_info
from requests.exceptions import HTTPError, ConnectionError


class NexusError(Exception):
    pass


class NexusHelper(object):

    # Constructor
    def __init__(self, sandbox=False, no_int=False, verbose=False):
        self.sandbox = sandbox
        self.no_int = no_int
        self.verbose = verbose
        self.config_file = os.path.join(os.path.expanduser('~'), ".nexus")
        self.nexus_endpoint = self.get_nexus_endpoint()

    def verify_nexus_access_token(self, user_input):
        access_token = user_input
        if access_token is None:
            access_token = self.get_nexus_access_token()
        self.nexus_test_api(access_token)
        self.save_nexus_access_token(access_token)
        return access_token

    def get_nexus_access_token(self):
        json_creds = self.read_credentials()
        if json_creds.get(self.config_token_property_name()):
            return json_creds.get(self.config_token_property_name())
        if self.no_int:
            raise_error(NexusError, "Cannot find Nexus credentials.")
        prompt = ("Please enter your Nexus access token (it will be "
                  "saved in {0} for future use): ".format(self.config_file))
        try:
            return raw_input(prompt)  # Python 2
        except NameError:
            return input(prompt)  # Python 3

    def save_nexus_access_token(self, access_token):
        json_creds = self.read_credentials()
        json_creds[self.config_token_property_name()] = access_token
        with open(self.config_file, 'w') as f:
            f.write(json.dumps(json_creds, indent=4, sort_keys=True))
        if self.verbose:
            print_info("Nexus access token saved in {0}".
                       format(self.config_file))

    def get_nexus_endpoint(self):
        # change once nexus is setup
        endpoint = "https://sandbox.bluebrainnexus.io/v1" if self.sandbox \
            else "https://sandbox.bluebrainnexus.io/v1"
        if self.verbose:
            print_info("Using Nexus endpoint {0}"
                       .format(endpoint))
        return endpoint

    def config_token_property_name(self):
        if self.sandbox:
            return "nexus-access-token-test"
        return "nexus-access-token"

    def read_credentials(self):
        try:
            with open(self.config_file, "r") as f:
                json_creds = json.load(f)
        except IOError:
            json_creds = {}
        except ValueError:
            json_creds = {}
        return json_creds

    def nexus_test_api(self, access_token):

        # Test connection to endpoint without token
        nexus.config.set_environment(self.nexus_endpoint)
        try:
            nexus.permissions.fetch()
        except ConnectionError as e:
            raise_error(NexusError,
                        "Cannot access Nexus endpoint", e.response)
        if self.verbose:
            print_info("Nexus endpoint is accessible")

        # Test authentication with token
        nexus.config.set_token(access_token)
        try:
            nexus.organizations.fetch("boutiques")
            if self.verbose:
                print_info("Authentication to Nexus successful")
        except HTTPError as e:
            if 404 == e.response.status_code:
                raise_error(NexusError,
                            "No organization called 'boutiques' "
                            "in Nexus repository", e.response)
            elif 401 == e.response.status_code:
                raise_error(NexusError,
                            "Cannot authenticate to Nexus API, check "
                            "your access token", e.response)
            else:
                raise_error(NexusError, "Something went wrong", e.response)
