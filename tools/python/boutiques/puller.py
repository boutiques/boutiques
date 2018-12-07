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

    def __init__(self, zid, verbose, download, sandbox, no_int):
        # remove zenodo prefix
        try:
            self.zid = zid.split(".", 1)[1]
        except IndexError:
            raise_error(ZenodoError, "Zenodo ID must be prefixed by "
                        "'zenodo', e.g. zenodo.123456")
        self.verbose = verbose
        self.download = download
        self.sandbox = sandbox
        self.no_int = no_int
        self.cache_dir = os.path.join(os.path.expanduser('~'), ".cache",
                                      "boutiques")

    def pull(self):
        from boutiques.searcher import Searcher
        searcher = Searcher(self.zid, self.verbose, self.sandbox, None, True)
        r = searcher.zenodo_search()

        for hit in r.json()["hits"]["hits"]:
            file_path = hit["files"][0]["links"]["self"]
            file_name = file_path.split(os.sep)[-1]
            if hit["id"] == int(self.zid):
                if self.download:
                    if not os.path.exists(self.cache_dir):
                        os.makedirs(self.cache_dir)
                    elif(not self.no_int and
                         os.path.isfile(os.path.join(self.cache_dir,
                                                     file_name))):
                        prompt = ("Found existing file with the same name. "
                                  "Overwrite? (Y/n) ")
                        try:
                            ret = raw_input(prompt)  # Python 2
                        except NameError:
                            ret = input(prompt)  # Python 3
                        if ret.upper() != "Y":
                            return
                    if(self.verbose):
                        print_info("Downloading descriptor %s"
                                   % file_name)
                    downloaded = urlretrieve(file_path,
                                             os.path.join(self.cache_dir,
                                                          file_name))
                    print("Downloaded descriptor to " + self.cache_dir)
                    return downloaded
                if(self.verbose):
                    print_info("Opening descriptor %s"
                               % file_name)
                # use the cached file if it exists
                if os.path.isfile(os.path.join(self.cache_dir, file_name)):
                    return open(os.path.join(self.cache_dir, file_name), "r")
                return urlopen(file_path)

        raise_error(ZenodoError, "Descriptor not found")
