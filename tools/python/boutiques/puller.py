import requests
import urllib
import os
from boutiques.logger import raise_error, print_info
from boutiques.publisher import ZenodoError
try:
    # Python 3
    from urllib.request import urlopen
    from urllib.request import urlretrieve
except ImportError:
    # Python 2
    from urllib2 import urlopen
    from urllib import urlretrieve


class Puller():

    def __init__(self, zid, verbose=False, sandbox=False):
        # remove zenodo prefix
        try:
            self.zid = zid.split(".", 1)[1]
        except IndexError:
            raise_error(ZenodoError, "Zenodo ID must be prefixed by "
                        "'zenodo', e.g. zenodo.123456")
        self.verbose = verbose
        self.sandbox = sandbox
        self.cache_dir = os.path.join(os.path.expanduser('~'), ".cache",
                                      "boutiques")
        self.cached_fname = os.path.join(self.cache_dir,
                                         "zenodo-{0}.json".format(self.zid))

    def pull(self):
        # return cached file if it exists
        if os.path.isfile(self.cached_fname):
            if(self.verbose):
                print_info("Found cached file at %s"
                           % self.cached_fname)
            return self.cached_fname

        from boutiques.searcher import Searcher
        searcher = Searcher(self.zid, self.verbose, self.sandbox,
                            exact_match=True)
        r = searcher.zenodo_search()

        for hit in r.json()["hits"]["hits"]:
            file_path = hit["files"][0]["links"]["self"]
            file_name = file_path.split(os.sep)[-1]
            if hit["id"] == int(self.zid):
                if not os.path.exists(self.cache_dir):
                    os.makedirs(self.cache_dir)
                if(self.verbose):
                    print_info("Downloading descriptor %s"
                               % file_name)
                downloaded = urlretrieve(file_path, self.cached_fname)
                print("Downloaded descriptor to " + downloaded[0])
                return downloaded[0]
        raise_error(ZenodoError, "Descriptor not found")
