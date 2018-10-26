import requests
import urllib
try:
    # Python 3
    from urllib.request import urlopen
    from urllib.request import urlretrieve
except ImportError:
    # Python 2
    from urllib2 import urlopen
    from urllib import urlretrieve


class ZenodoError(Exception):
    pass


class Puller():

    def __init__(self, identifier, verbose, download):
        self.identifier = identifier
        self.verbose = verbose
        self.download = download

    def pull(self):
        r = requests.get('https://zenodo.org/api/records/?q=boutiques&'
                         'keywords=boutiques&keywords=schema&'
                         'keywords=version&file_type=json&type=software')

        if(r.status_code != 200):
            self.raise_zenodo_error("Error searching Zenodo", r)

        try:
            int(self.identifier)
            return self.pull_by_id(r, self.identifier)
        except ValueError:
            return self.pull_by_filename(r, self.identifier)

    def pull_by_id(self, r, zid):
        for hit in r.json()["hits"]["hits"]:
            file_path = hit["files"][0]["links"]["self"]
            file_name = file_path.split("/")[-1]
            if hit["id"] == int(zid):
                if self.download:
                    if(self.verbose):
                        self.print_zenodo_info("Downloading descriptor %s"
                                               % file_name, r)
                    return urlretrieve(file_path, file_name)
                if(self.verbose):
                    self.print_zenodo_info("Opening descriptor %s"
                                           % file_name, r)
                return urlopen(file_path)

        raise IOError("Descriptor not found")

    def pull_by_filename(self, r, filename):
        for hit in r.json()["hits"]["hits"]:
            file_path = hit["files"][0]["links"]["self"]
            file_name = file_path.split("/")[-1]
            if file_name == filename:
                if self.download:
                    if(self.verbose):
                        self.print_zenodo_info("Downloading descriptor %s"
                                               % file_name, r)
                    return urlretrieve(file_path, file_name)
                if(self.verbose):
                    self.print_zenodo_info("Opening descriptor %s"
                                           % file_name, r)
                return urlopen(file_path)

        raise IOError("Descriptor not found")

    def print_zenodo_info(self, message, r):
        print("[ INFO ({1}) ] {0}".format(message, r.status_code))

    def raise_zenodo_error(self, message, r):
        raise ZenodoError("Zenodo error ({0}): {1}."
                          .format(r.status_code, message))
