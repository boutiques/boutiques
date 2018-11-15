import requests
import urllib
import os
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

    def __init__(self, zid, verbose, download, sandbox):
        # remove zenodo prefix
        try:
            self.zid = zid.split(".", 1)[1]
        except IndexError:
            raise ZenodoError("Zenodo ID must be prefixed by "
                              "'zenodo', e.g. zenodo.123456")
        self.verbose = verbose
        self.download = download
        self.sandbox = sandbox

    def pull(self):
        from boutiques.searcher import Searcher
        searcher = Searcher(None, self.verbose, self.sandbox)
        r = searcher.zenodo_search()

        for hit in r.json()["hits"]["hits"]:
            file_path = hit["files"][0]["links"]["self"]
            file_name = file_path.split(os.sep)[-1]
            if hit["id"] == int(self.zid):
                if self.download:
                    cache_dir = os.path.join(os.path.expanduser('~'), ".cache",
                                             "boutiques")
                    if not os.path.exists(cache_dir):
                        os.makedirs(cache_dir)
                    if(self.verbose):
                        self.print_zenodo_info("Downloading descriptor %s"
                                               % file_name, r)
                    return urlretrieve(file_path, os.path.join(cache_dir,
                                       file_name))
                if(self.verbose):
                    self.print_zenodo_info("Opening descriptor %s"
                                           % file_name, r)
                return urlopen(file_path)

        raise ZenodoError("Descriptor not found")

    def print_zenodo_info(self, message, r):
        print("[ INFO ({1}) ] {0}".format(message, r.status_code))

    def raise_zenodo_error(self, message, r):
        raise ZenodoError("Zenodo error ({0}): {1}."
                          .format(r.status_code, message))
