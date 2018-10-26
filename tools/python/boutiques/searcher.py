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
        r = requests.get('https://zenodo.org/api/records/?q=%s&'
                         'keywords=boutiques&keywords=schema&'
                         'keywords=version&file_type=json&type=software'
                         % self.query)
        if(r.status_code != 200):
            self.raise_zenodo_error("Error searching Zenodo", r)

        if(self.verbose):
            self.print_zenodo_info("Zenodo search returned %d results"
                                   % r.json()["hits"]["total"], r)

        return self.create_results_table(r.json())

    def create_results_table(self, results):
        table = []
        for hit in results["hits"]["hits"]:
            table.append([hit["id"], hit["metadata"]["title"],
                         hit["metadata"]["description"]])
        return tabulate(table, headers=['ID', 'TITLE',
                        'DESCRIPTION'], tablefmt='plain')

    def print_zenodo_info(self, message, r):
        print("[ INFO ({1}) ] {0}".format(message, r.status_code))

    def raise_zenodo_error(self, message, r):
        raise ZenodoError("Zenodo error ({0}): {1}."
                          .format(r.status_code, message))
