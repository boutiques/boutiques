#!/usr/bin/env python

import requests
from collections import OrderedDict
import json
from operator import itemgetter
from boutiques.logger import raise_error, print_info
from boutiques.publisher import ZenodoError


class Searcher():

    def __init__(self, query, verbose=False, sandbox=False, max_results=None,
                 no_trunc=False, exact_match=False):
        if query is not None:
            self.query = query
        else:
            self.query = 'boutiques'

        if not exact_match:
            self.query = '*' + self.query + '*'

        self.verbose = verbose
        self.sandbox = sandbox
        self.no_trunc = no_trunc
        self.max_results = max_results

        # Return max 10 results by default
        if max_results is None:
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
            (id, title, description, downloads) = self.parse_basic_info(hit)
            result_dict = OrderedDict([("ID", id), ("TITLE", title),
                                      ("DESCRIPTION", description),
                                      ("DOWNLOADS", downloads)])
            if not self.no_trunc:
                result_dict = self.truncate(result_dict, 40)
            results_list.append(result_dict)
        results_list = sorted(results_list, key=itemgetter('DOWNLOADS'),
                              reverse=True)
        return results_list

    def create_results_list_verbose(self, results):
        results_list = []
        for hit in results["hits"]["hits"]:
            (id, title, description, downloads) = self.parse_basic_info(hit)
            author = hit["metadata"]["creators"][0]["name"]
            version = hit["metadata"]["version"]
            doi = hit["doi"]
            keyword_data = self.get_keyword_data(hit["metadata"]["keywords"])
            schema_version = keyword_data["schema-version"]
            container = keyword_data["container-type"]
            other_tags = ",".join(keyword_data["other"])
            result_dict = OrderedDict([("ID", id),
                                      ("TITLE", title),
                                      ("DESCRIPTION", description),
                                      ("DOWNLOADS", downloads),
                                      ("AUTHOR", author),
                                      ("VERSION", version),
                                      ("DOI", doi),
                                      ("SCHEMA VERSION", schema_version),
                                      ("CONTAINER", container),
                                      ("TAGS", other_tags)])
            if not self.no_trunc:
                result_dict = self.truncate(result_dict, 40)
            results_list.append(result_dict)
        results_list = sorted(results_list, key=itemgetter('DOWNLOADS'),
                              reverse=True)
        return results_list

    def parse_basic_info(self, hit):
        id = "zenodo." + str(hit["id"])
        title = hit["metadata"]["title"]
        description = hit["metadata"]["description"]
        downloads = hit["stats"]["version_downloads"]
        return (id, title, description, downloads)

    # truncates every value of a dictionary whose length is
    # greater than max_length
    def truncate(self, d, max_length):
        for k, v in list(d.items()):
            if len(str(v)) > max_length:
                d[k] = v[:max_length] + "..."
        return d

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
