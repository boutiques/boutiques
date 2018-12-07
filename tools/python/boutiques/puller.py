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

    def __init__(self, zid, verbose, download, sandbox):
        # remove zenodo prefix
        try:
            self.zid = zid.split(".", 1)[1]
        except IndexError:
            raise_error(ZenodoError, "Zenodo ID must be prefixed by "
                        "'zenodo', e.g. zenodo.123456")
        self.verbose = verbose
        self.download = download
        self.sandbox = sandbox

    def pull(self):
        from boutiques.searcher import Searcher
        searcher = Searcher(self.zid, self.verbose, self.sandbox, None)
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
                        print_info("Downloading descriptor %s"
                                   % file_name)
                    downloaded = urlretrieve(file_path, os.path.join(cache_dir,
                                             file_name))
                    print_info("Downloaded descriptor to " + cache_dir)
                    return downloaded
                if(self.verbose):
                    print_info("Opening descriptor %s"
                               % file_name)
                return urlopen(file_path)

        raise_error(ZenodoError, "Descriptor not found")
