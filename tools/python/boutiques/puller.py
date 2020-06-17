import requests
import urllib
import os
from boutiques.logger import raise_error, print_info
from boutiques.searcher import Searcher
from boutiques.zenodoHelper import ZenodoError, ZenodoHelper

try:
    # Python 3
    from urllib.request import urlopen
    from urllib.request import urlretrieve
except ImportError:
    # Python 2
    from urllib2 import urlopen
    from urllib import urlretrieve


class Puller():

    def __init__(self, zids, verbose=False, sandbox=False):
        # remove zenodo prefix
        self.zenodo_entries = []
        self.cache_dir = os.path.join(
            os.path.expanduser('~'), ".cache", "boutiques",
            "sandbox" if sandbox else "production")
        discarded_zids = zids
        # This removes duplicates, should maintain order
        zids = list(dict.fromkeys(zids))
        for zid in zids:
            discarded_zids.remove(zid)
            try:
                # Zenodo returns the full DOI, but for the purposes of
                # Boutiques we just use the Zenodo-specific portion (as its the
                # unique part). If the API updates on Zenodo to no longer
                # provide the full DOI, this still works because it just grabs
                # the last thing after the split.
                zid = zid.split('/')[-1]
                newzid = zid.split(".", 1)[1]
                newfname = os.path.join(self.cache_dir,
                                        "zenodo-{0}.json".format(newzid))
                self.zenodo_entries.append({"zid": newzid, "fname": newfname})
            except IndexError:
                raise_error(ZenodoError, "Zenodo ID must be prefixed by "
                            "'zenodo', e.g. zenodo.123456")
        self.verbose = verbose
        self.sandbox = sandbox
        if(self.verbose):
            for zid in discarded_zids:
                print_info("Discarded duplicate id {0}".format(zid))
        self.zenodo_helper = ZenodoHelper(sandbox=self.sandbox,
                                          verbose=self.verbose)

    def pull(self):
        # return cached file if it exists
        json_files = []
        for entry in self.zenodo_entries:
            if os.path.isfile(entry["fname"]):
                if(self.verbose):
                    print_info("Found cached file at %s"
                               % entry["fname"])
                json_files.append(entry["fname"])
                continue

            searcher = Searcher(entry["zid"], self.verbose, self.sandbox,
                                exact_match=True)
            r = self.zenodo_helper.zenodo_search(searcher.query,
                                                 searcher.query_line)
            if not len(r.json()["hits"]["hits"]):
                raise_error(ZenodoError, "Descriptor \"{0}\" "
                            "not found".format(entry["zid"]))
            for hit in r.json()["hits"]["hits"]:
                file_path = hit["files"][0]["links"]["self"]
                file_name = file_path.split(os.sep)[-1]
                if hit["id"] == int(entry["zid"]):
                    if not os.path.exists(self.cache_dir):
                        os.makedirs(self.cache_dir)
                    if(self.verbose):
                        print_info("Downloading descriptor %s"
                                   % file_name)
                    downloaded = urlretrieve(file_path, entry["fname"])
                    if(self.verbose):
                        print_info("Downloaded descriptor to "
                                   + downloaded[0])
                    json_files.append(downloaded[0])
                else:
                    raise_error(ZenodoError, "Searched-for descriptor \"{0}\" "
                                "does not match descriptor \"{1}\" returned "
                                "from Zenodo".format(entry["zid"], hit["id"]))

        return json_files
