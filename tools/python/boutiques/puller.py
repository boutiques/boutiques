import requests
import urllib


class ZenodoError(Exception):
    pass


class Puller():

    def __init__(self, zid, verbose):
        self.zid = zid
        self.verbose = verbose

    def pull(self):
        r = requests.get('https://zenodo.org/api/records/?q=boutiques&'
                         'keywords=boutiques&keywords=schema&'
                         'keywords=version&file_type=json&type=software')

        if(r.status_code != 200):
            self.raise_zenodo_error("Error searching Zenodo", r)

        for hit in r.json()["hits"]["hits"]:
            if hit["id"] == int(self.zid):
                file_path = hit["files"][0]["links"]["self"]
                file_name = file_path.split("/")[-1]
                urllib.urlretrieve(file_path, file_name)
                if(self.verbose):
                    self.print_zenodo_info("Downloaded descriptor %s"
                                           % file_name, r)
                return

        return "Descriptor not found"

    def print_zenodo_info(self, message, r):
        print("[ INFO ({1}) ] {0}".format(message, r.status_code))

    def raise_zenodo_error(self, message, r):
        raise ZenodoError("Zenodo error ({0}): {1}."
                          .format(r.status_code, message))
