#!/usr/bin/env python

import sys
from collections import OrderedDict
import numbers
from operator import itemgetter
from boutiques.logger import raise_error, print_info
from boutiques.publisher import ZenodoError
from boutiques.zenodoHelper import ZenodoHelper
from urllib.parse import quote


class Searcher():

    def __init__(self, query, verbose=False, sandbox=False, max_results=None,
                 no_trunc=False, exact_match=False):
        if query is not None:
            self.query = query
            self.query_line = ''
            if not exact_match:
                terms = self.query.replace('/', '.').split(" ")
                for t in terms:
                    uncased_term = ["[{0}]".format(ch.upper() + ch.lower()
                                                   if ch.isalpha() else ch)
                                    for ch in t]
                    uncased_term = quote("".join(uncased_term))
                    self.query_line += ' AND (/.*%s.*/)' % uncased_term
            else:
                self.query_line = ' AND (/%s/)' % self.query.replace('/', '.')
        else:
            self.query = ''
            self.query_line = ''

        if(verbose):
            print_info("Using Query Line: " + self.query_line)

        self.verbose = verbose
        self.sandbox = sandbox
        self.no_trunc = no_trunc
        self.max_results = max_results
        self.zenodo_helper = ZenodoHelper(sandbox=self.sandbox,
                                          verbose=self.verbose)

        # Display top 10 results by default
        if max_results is None:
            self.max_results = 10

        # Zenodo will error if asked for more than 9999 results
        if self.max_results > 9999:
            self.max_results = 9999

        # Set Zenodo endpoint
        self.zenodo_endpoint = "https://sandbox.zenodo.org" if\
            self.sandbox else "https://zenodo.org"
        if(self.verbose):
            print_info("Using Zenodo endpoint {0}".
                       format(self.zenodo_endpoint))

    def search(self):
        results = self.zenodo_helper.zenodo_search(self.query, self.query_line)
        total_results = results.json()["hits"]["total"]
        total_deprecated = len([h['metadata']['keywords'] for h in
                                results.json()['hits']['hits'] if
                                'metadata' in h and
                                'keywords' in h['metadata'] and
                                'deprecated' in h['metadata']['keywords']])
        results_list = self.create_results_list_verbose(results.json()) if\
            self.verbose else\
            self.create_results_list(results.json())
        num_results = len(results_list)
        print_info("Showing %d of %d result(s)%s"
                   % (num_results if num_results < self.max_results
                      else self.max_results,
                      total_results if self.verbose
                      else total_results - total_deprecated,
                      "." if self.verbose
                      else ", excluding %d deprecated result(s)."
                      % total_deprecated))
        return results_list

    def create_results_list(self, results):
        results_list = []
        for hit in results["hits"]["hits"]:
            (id, title, description, downloads) = self.parse_basic_info(hit)
            # skip hit if result is deprecated
            keyword_data = self.get_keyword_data(hit["metadata"]["keywords"])
            if 'deprecated' in keyword_data['other']:
                continue
            result_dict = OrderedDict([("ID", id), ("TITLE", title),
                                      ("DESCRIPTION", description),
                                      ("DOWNLOADS", downloads)])
            if not self.no_trunc:
                result_dict = self.truncate(result_dict, 40)
            results_list.append(result_dict)
        results_list = sorted(results_list, key=itemgetter('DOWNLOADS'),
                              reverse=True)
        # Truncate the list according to the desired maximum number of results
        return results_list[:self.max_results]

    def create_results_list_verbose(self, results):
        results_list = []
        for hit in results["hits"]["hits"]:
            (id, title, description, downloads) = self.parse_basic_info(hit)
            author = hit["metadata"]["creators"][0]["name"]
            version = hit["metadata"].get("version", "unknown")
            publication_date = hit["metadata"]['publication_date']
            doi = hit["doi"]
            keyword_data = self.get_keyword_data(hit["metadata"]["keywords"])
            schema_version = keyword_data["schema-version"]
            container = keyword_data["container-type"]
            other_tags = ",".join(keyword_data["other"])
            result_dict = OrderedDict([("ID", id),
                                      ("TITLE", title),
                                      ("DESCRIPTION", description),
                                      ("PUBLICATION DATE", publication_date),
                                      ("DEPRECATED", 'deprecated' in
                                       keyword_data['other']),
                                      ("DOWNLOADS", downloads),
                                      ("AUTHOR", author),
                                      ("VERSION", version),
                                      ("DOI", doi),
                                      ("SCHEMA VERSION", schema_version),
                                      ("CONTAINER", container),
                                      ("TAGS", other_tags)])
            if sys.stdout.encoding.lower != "UTF-8":
                for k, v in list(result_dict.items()):
                    if isinstance(v, str):
                        result_dict[k] = \
                            v.encode('ascii', 'xmlcharrefreplace').decode()
            if not self.no_trunc:
                result_dict = self.truncate(result_dict, 40)
            results_list.append(result_dict)
        results_list = sorted(results_list, key=itemgetter('DOWNLOADS'),
                              reverse=True)
        # Truncate the list according to the desired maximum number of results
        return results_list[:self.max_results]

    def parse_basic_info(self, hit):
        id = "zenodo." + str(hit["id"])
        title = hit["metadata"]["title"]
        description = hit["metadata"]["description"]
        downloads = 0
        if "version_downloads" in hit["stats"]:
            downloads = hit["stats"]["version_downloads"]
        return (id, title, description, downloads)

    # truncates every value of a dictionary whose length is
    # greater than max_length
    def truncate(self, d, max_length):
        for k, v in list(d.items()):
            if isinstance(v, numbers.Number):
                v = str(v)
            if len(v) > max_length:
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
