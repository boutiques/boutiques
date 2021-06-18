#!/usr/bin/env python
import os
from codecs import open

import simplejson as json
from boutiques.util.utils import importCatcher
from boutiques.logger import raise_error, print_info


class NexusError(Exception):
    pass


class NexusHelper(object):

    # Constructor
    def __init__(self, sandbox=False, no_int=False, verbose=False):
        try:
            import nexussdk as nexus
        except ImportError:
            raise_error(NexusError,
                        "Cannot import nexussdk, "
                        "consider upgrading to python 3.5 or higher")
            return

        self.nexus = nexus
        self.sandbox = sandbox
        self.no_int = no_int
        self.verbose = verbose
        self.config_file = self.get_config_file()
        self.nexus_endpoint = self.get_nexus_endpoint()

    def verify_nexus_input(self, input_token, input_org, input_project):
        access_token = input_token
        org = input_org
        project = input_project
        if access_token is None:
            access_token = self.get_nexus_access_token()
        if org is None:
            org = self.get_nexus_organization()
        if project is None:
            project = self.get_nexus_project()
        self.nexus_test_api(access_token, org, project)
        self.save_nexus_inputs(access_token, org, project)
        return access_token, org, project

    def get_nexus_access_token(self):
        json_creds = self.read_credentials()
        if json_creds.get(self.config_token_property_name()):
            return json_creds.get(self.config_token_property_name())
        if self.no_int:
            raise_error(NexusError, "Cannot find Nexus credentials.")
        prompt = ("Please enter your Nexus access token (it will be "
                  "saved in {0} for future use): ".format(self.config_file))
        return self.prompt(prompt)

    def get_nexus_organization(self):
        json_creds = self.read_credentials()
        if json_creds.get("nexus-organization"):
            return json_creds.get("nexus-organization")
        if self.no_int:
            raise_error(NexusError, "Cannot find Nexus organization.")
        prompt = ("Please enter the Nexus organization you want to publish to"
                  " (it will be saved in {0} for future use): "
                  .format(self.config_file))
        return self.prompt(prompt)

    def get_nexus_project(self):
        json_creds = self.read_credentials()
        if json_creds.get("nexus-project"):
            return json_creds.get("nexus-project")
        if self.no_int:
            raise_error(NexusError, "Cannot find Nexus project.")
        prompt = ("Please enter the Nexus project you want to publish to"
                  " (it will be saved in {0} for future use): "
                  .format(self.config_file))
        return self.prompt(prompt)

    def save_nexus_inputs(self, access_token, org, project):
        json_creds = self.read_credentials()
        json_creds[self.config_token_property_name()] = access_token
        json_creds["nexus-organization"] = org
        json_creds["nexus-project"] = project
        with open(self.config_file, 'w') as f:
            f.write(json.dumps(json_creds, indent=4, sort_keys=True))
        if self.verbose:
            print_info("Nexus access token, organization and project"
                       " saved in {0}".format(self.config_file))

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

    @importCatcher()
    def nexus_test_api(self, access_token, org, project):
        from requests.exceptions import HTTPError, ConnectionError
        # Test connection to endpoint without token
        self.nexus.config.set_environment(self.nexus_endpoint)
        try:
            self.nexus.permissions.fetch()
        except ConnectionError as e:
            raise_error(NexusError,
                        "Cannot access Nexus endpoint", e.response)
        if self.verbose:
            print_info("Nexus endpoint is accessible")

        # Test authentication with token, org and project
        self.nexus.config.set_token(access_token)
        try:
            self.nexus.projects.fetch(org, project)
            if self.verbose:
                print_info("Authentication to Nexus successful")
        except HTTPError as e:
            if 404 == e.response.status_code:
                raise_error(NexusError,
                            "No project '{}' in organization '{}' "
                            "in Nexus repository".format(project, org),
                            e.response)
            elif 401 == e.response.status_code:
                raise_error(NexusError,
                            "Cannot authenticate to Nexus API, check "
                            "your access token", e.response)
            else:
                raise_error(NexusError, "Something went wrong", e.response)

    def get_config_file(self):
        return os.path.join(os.path.expanduser('~'), ".nexus")

    def prompt(self, prompt):
        try:
            return raw_input(prompt)  # Python 2
        except NameError:
            return input(prompt)  # Python 3

    def publish(self, org_label, project_label, filepath):
        self.nexus.files.create(org_label, project_label, filepath)
