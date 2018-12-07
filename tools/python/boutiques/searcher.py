#!/usr/bin/env python

import requests
from collections import OrderedDict
import json
from boutiques.logger import raise_error, print_info
from boutiques.publisher import ZenodoError


class Searcher():

    def __init__(self, query, verbose, sandbox, max_results):
        if query is not None:
            self.query = query
        else:
            self.query = 'boutiques'

        self.verbose = verbose
        self.sandbox = sandbox

        # Return max 10 results by default
        if max_results is not None:
            self.max_results = max_results
        else:
            self.max_results = 10

        # Set Zenodo endpoint
        self.zenodo_endpoint = "https://sandbox.zenodo.org" if\
            self.sandbox else "https://zenodo.org"
        if(self.verbose):
            print_info("Using Zenodo endpoint {0}".
                       format(self.zenodo_endpoint))

    def search(self):
        results = self.zenodo_search()
        print_info("Showing %d of %d results."
                   % (len(results.json()["hits"]["hits"]),
                      results.json()["hits"]["total"]))
        if self.verbose:
            return self.create_results_list_verbose(results.json())
        return self.create_results_list(results.json())

    def zenodo_search(self):
        r = requests.get(self.zenodo_endpoint + '/api/records/?q=%s&'
                         'keywords=boutiques&keywords=schema&'
                         'keywords=version&file_type=json&type=software'
                         '&page=1&size=%s' % (self.query, self.max_results))
        if(r.status_code != 200):
            raise_error(ZenodoError, "Error searching Zenodo", r)
        if(self.verbose):
            print_info("Search successful.", r)
        return r

    def create_results_list(self, results):
        results_list = []
        for hit in results["hits"]["hits"]:
            id = "zenodo." + str(hit["id"])
            title = hit["metadata"]["title"]
            description = hit["metadata"]["description"]
            results_list.append(OrderedDict([("ID", id), ("TITLE", title),
                                ("DESCRIPTION", description)]))
        return results_list

    def create_results_list_verbose(self, results):
        results_list = []
        for hit in results["hits"]["hits"]:
            id = "zenodo." + str(hit["id"])
            title = hit["metadata"]["title"]
            description = hit["metadata"]["description"]
            author = hit["metadata"]["creators"][0]["name"]
            version = hit["metadata"]["version"]
            doi = hit["doi"]
            keyword_data = self.get_keyword_data(hit["metadata"]["keywords"])
            schema_version = keyword_data["schema-version"]
            container = keyword_data["container-type"]
            other_tags = ",".join(keyword_data["other"])
            results_list.append(OrderedDict([
                                ("ID", id),
                                ("TITLE", title),
                                ("DESCRIPTION", description),
                                ("AUTHOR", author),
                                ("VERSION", version),
                                ("DOI", doi),
                                ("SCHEMA VERSION", schema_version),
                                ("CONTAINER", container),
                                ("TAGS", other_tags)]))
        return results_list

    def get_keyword_data(self, keywords):
        keyword_data = {"container-type": "None", "other": []}
        for keyword in keywords:
            if keyword.split(":")[0] == "schema-version":
                keyword_data["schema-version"] = keyword.split(":")[1]
            elif (keyword.lower() == "docker" or
                  keyword.lower() == "singularity"):
                keyword_data["container-type"] = keyword
            else:
                keyword_data["other"].append(keyword)
        return keyword_data
