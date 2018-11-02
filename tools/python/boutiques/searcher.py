import requests
from tabulate import tabulate


class ZenodoError(Exception):
    pass


class Searcher():

    def __init__(self, query, verbose):
        if query is not None:
            self.query = query
        else:
            self.query = 'boutiques'

        self.verbose = verbose

    def search(self):
        results = self.zenodo_search()
        if self.verbose:
            return self.create_results_table_verbose(results.json())
        return self.create_results_table(results.json())

    def zenodo_search(self):
        r = requests.get('https://zenodo.org/api/records/?q=%s&'
                         'keywords=boutiques&keywords=schema&'
                         'keywords=version&file_type=json&type=software'
                         % self.query)
        if(r.status_code != 200):
            self.raise_zenodo_error("Error searching Zenodo", r)

        if(self.verbose):
            self.print_zenodo_info("Zenodo search returned %d results"
                                   % r.json()["hits"]["total"], r)
        return r

    def create_results_table(self, results):
        table = []
        for hit in results["hits"]["hits"]:
            id = "zenodo." + str(hit["id"])
            title = hit["metadata"]["title"]
            description = hit["metadata"]["description"]
            table.append([id, title, description])
        return tabulate(table, headers=['ID', 'TITLE',
                        'DESCRIPTION'], tablefmt='plain')

    def create_results_table_verbose(self, results):
        table = []
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

            table.append([id, title, description, author, version,
                         doi, schema_version, container, other_tags])
        return tabulate(table, headers=['ID', 'TITLE',
                                        'DESCRIPTION', 'AUTHOR', 'VERSION',
                                        'DOI', 'SCHEMA VERSION', 'CONTAINER',
                                        'TAGS'],
                        tablefmt='plain')

    def print_zenodo_info(self, message, r):
        print("[ INFO ({1}) ] {0}".format(message, r.status_code))

    def raise_zenodo_error(self, message, r):
        raise ZenodoError("Zenodo error ({0}): {1}."
                          .format(r.status_code, message))

    def get_keyword_data(self, keywords):
        keyword_data = {"container-type": "None", "other": []}
        for keyword in keywords:
            if keyword.split(":")[0] == "schema-version":
                keyword_data["schema-version"] = keyword.split(":")[1]
            elif keyword.lower() == "docker" or
            keyword.lower() == "singularity":
                keyword_data["container-type"] = keyword
            else:
                keyword_data["other"].append(keyword)
        return keyword_data
