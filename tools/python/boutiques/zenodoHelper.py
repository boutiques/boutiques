#!/usr/bin/env python
import os
import re
import simplejson as json
import requests
import sys
import numbers
from boutiques.logger import raise_error, print_info
from collections import OrderedDict
from operator import itemgetter
from urllib.request import urlretrieve


class ZenodoError(Exception):
    pass


class ZenodoHelper(object):

    # Constructor
    def __init__(self, sandbox=False, no_int=False, verbose=False,
                 no_trunc=False, max_results=sys.maxsize):
        self.sandbox = sandbox
        self.no_int = no_int
        self.verbose = verbose
        self.config_file = os.path.join(os.path.expanduser('~'), ".boutiques")
        self.zenodo_endpoint = self.get_zenodo_endpoint()
        self.no_trunc = no_trunc
        self.max_results = max_results

    def verify_zenodo_access_token(self, user_input):
        access_token = user_input
        if access_token is None:
            access_token = self.get_zenodo_access_token()
        self.zenodo_test_api(access_token)
        self.save_zenodo_access_token(access_token)
        return access_token

    def get_zenodo_access_token(self):
        json_creds = self.read_credentials()
        if json_creds.get(self.config_token_property_name()):
            return json_creds.get(self.config_token_property_name())
        if (self.no_int):
            raise_error(ZenodoError, "Cannot find Zenodo credentials.")
        prompt = ("Please enter your Zenodo access token (it will be "
                  "saved in {0} for future use): ".format(self.config_file))
        try:
            return raw_input(prompt)  # Python 2
        except NameError:
            return input(prompt)  # Python 3

    def save_zenodo_access_token(self, access_token):
        json_creds = self.read_credentials()
        json_creds[self.config_token_property_name()] = access_token
        with open(self.config_file, 'w') as f:
            f.write(json.dumps(json_creds, indent=4, sort_keys=True))
        if (self.verbose):
            print_info("Zenodo access token saved in {0}".
                       format(self.config_file))

    def get_zenodo_endpoint(self):
        endpoint = "https://sandbox.zenodo.org" if self.sandbox \
            else "https://zenodo.org"
        if (self.verbose):
            print_info("Using Zenodo endpoint {0}"
                       .format(endpoint))
        return endpoint

    def record_exists(self, record_id):
        r = requests.get(self.zenodo_endpoint +
                         '/api/records/{}'.format(record_id))
        if r.status_code == 200:
            return True
        if r.status_code == 404:
            return False
        raise_error(ZenodoError,
                    "Cannot test existence of record {}".format(record_id), r)

    def zenodo_get_record(self, zenodo_id):
        r = requests.get(self.zenodo_endpoint +
                         '/api/records/{}'.format(zenodo_id))
        if r.status_code != 200:
            raise_error(ZenodoError,
                        "File \"{}\" not found".format(zenodo_id), r)
        return r.json()

    def get_record_id_from_zid(self, zenodo_id):
        '''
        zenodo_id is in the form zenodo.1234567
        record id is 1234567
        '''
        if not re.match(r'zenodo\.[0-9]', zenodo_id):
            raise_error(ZenodoError,
                        'This does not look like a valid Zenodo ID: {}.'
                        'Zenodo ids must be in the form zenodo.1234567'
                        .format(zenodo_id))
        parts = zenodo_id.split('.')
        return parts[1]

    def get_zid_from_filename(self, filename):
        # Filename must be in the form /a/b/c/zenodo-1234.json
        # where zenodo.1234 is the record id.
        basename = os.path.basename(filename)
        if not re.match(r'zenodo-[0-9]*\.json', basename):
            raise_error(ZenodoError,
                        'This does not look like a valid file name: {}'
                        .format(filename))
        return basename.replace('.json', '').replace('-', '.')

    def get_doi_from_zid(self, zenodo_id):
        prefix = "10.5072" if self.sandbox else "10.5281"
        return '{}/{}'.format(prefix, zenodo_id)

    def config_token_property_name(self):
        if self.sandbox:
            return "zenodo-access-token-test"
        return "zenodo-access-token"

    def read_credentials(self):
        try:
            with open(self.config_file, "r") as f:
                json_creds = json.load(f)
        except IOError:
            json_creds = {}
        except ValueError:
            json_creds = {}
        return json_creds

    def zenodo_test_api(self, access_token):
        r = requests.get(self.zenodo_endpoint+'/api/deposit/depositions')
        if(r.status_code != 401):
            raise_error(ZenodoError, "Cannot access Zenodo", r)
        if(self.verbose):
            print_info("Zenodo is accessible", r)
        r = requests.get(self.zenodo_endpoint+'/api/deposit/depositions',
                         params={'access_token': access_token})
        message = "Cannot authenticate to Zenodo API, check your access token"
        if(r.status_code != 200):
            raise_error(ZenodoError, message, r)
        if(self.verbose):
            print_info("Authentication to Zenodo successful", r)

    def zenodo_deposit(self, metadata, access_token):
        headers = {"Content-Type": "application/json"}
        data = metadata
        r = requests.post(self.zenodo_endpoint+'/api/deposit/depositions',
                          params={'access_token': access_token},
                          json={},
                          data=json.dumps(data),
                          headers=headers)
        if(r.status_code != 201):
            raise_error(ZenodoError, "Deposition failed", r)
        zid = r.json()['id']
        if(self.verbose):
            print_info("Deposition succeeded, id is {0}".
                       format(zid), r)
        return zid

    def zenodo_deposit_updated_version(self, metadata,
                                       access_token, deposition_id):
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/actions/newversion'
                          % deposition_id,
                          params={'access_token': access_token})
        if r.status_code == 403:
            raise_error(ZenodoError, "You do not have permission to access "
                                     "this resource. Note that you cannot "
                                     "publish an update to a tool belonging "
                                     "to someone else.", r)
        elif(r.status_code != 201):
            raise_error(ZenodoError, "Deposition of new version failed. Check "
                                     "that the Zenodo ID is correct (if one "
                                     "was provided).", r)
        if(self.verbose):
            print_info("Deposition of new version succeeded", r)
        new_url = r.json()['links']['latest_draft']
        new_zid = new_url.split("/")[-1]
        self.zenodo_update_metadata(new_zid, r.json()['doi'],
                                    metadata, access_token)
        self.zenodo_delete_files(new_zid, r.json()["files"], access_token)
        return new_zid

    def zenodo_update_metadata(self, new_deposition_id, old_doi,
                               metadata, access_token):
        data = metadata

        # Add the new DOI to the metadata
        old_doi_split = old_doi.split(".")
        old_doi_split[-1] = new_deposition_id
        new_doi = '.'.join(old_doi_split)
        data['metadata']['doi'] = new_doi

        headers = {"Content-Type": "application/json"}
        r = requests.put(self.zenodo_endpoint+'/api/deposit/depositions/%s'
                         % new_deposition_id,
                         params={'access_token': access_token},
                         data=json.dumps(data),
                         headers=headers)
        if(r.status_code != 200):
            raise_error(ZenodoError, "Cannot update metadata of new version", r)
        if(self.verbose):
            print_info("Updated metadata of new version", r)

    # When a new version is created, the files from the old version are
    # automatically copied over. This method removes them.
    def zenodo_delete_files(self, new_deposition_id, files, access_token):
        for file in files:
            file_id = file["id"]
            r = requests.delete(self.zenodo_endpoint +
                                '/api/deposit/depositions/%s/files/%s'
                                % (new_deposition_id, file_id),
                                params={'access_token': access_token})
            if(r.status_code != 204):
                raise_error(ZenodoError, "Could not delete old file", r)
            if(self.verbose):
                print_info("Deleted old file", r)

    def zenodo_publish(self, access_token, deposition_id, msg_obj):
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/actions/publish'
                          % deposition_id,
                          params={'access_token': access_token})
        if(r.status_code != 202):
            raise_error(ZenodoError, "Cannot publish {}".format(msg_obj), r)
        if(self.verbose):
            print_info("{0} published to Zenodo, doi is {1}".
                       format(msg_obj, r.json()['doi']), r)
        return r.json()['doi']

    def search(self, query, query_line, firstKeyWord, secondKeyWord,
               searchType):
        results = self.zenodo_search(query, query_line, firstKeyWord,
                                     secondKeyWord, searchType)
        total_results = results.json()["hits"]["total"]
        total_deprecated = len([h['metadata']['keywords'] for h in
                                results.json()['hits']['hits'] if
                                'metadata' in h and
                                'keywords' in h['metadata'] and
                                'deprecated' in h['metadata']['keywords']])
        results_list = self.create_results_list_verbose(
            results.json(), searchType) if self.verbose else\
            self.create_results_list(results.json())
        num_results = len(results_list)
        print_info("Showing %d of %d result(s)%s"
                   % (num_results if num_results < self.max_results
                      else self.max_results,
                      total_results if self.verbose
                      else total_results - total_deprecated,
                      "." if self.verbose
                      else ", exluding %d deprecated result(s)."
                      % total_deprecated))
        return results_list

    def zenodo_search(self, query, query_line, firstKeyWord, secondKeyWord,
                      searchType):
        # Get all results
        r = requests.get(self.zenodo_endpoint + '/api/records/?q='
                         'keywords:(/%s/) AND '
                         'keywords:(/%s/) '
                         '%s'
                         '&file_type=json&type=%s&'
                         'page=1&size=%s' % (firstKeyWord, secondKeyWord,
                                             query_line, searchType, 9999))
        if(r.status_code != 200):
            raise_error(ZenodoError, "Error searching Zenodo", r)
        if(self.verbose):
            print_info("Search successful for query \"%s\"" % query, r)

        return r

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
        if self.max_results:
            return results_list[:self.max_results]
        else:
            return results_list

    def create_results_list_verbose(self, results, searchType):
        results_list = []
        for hit in results["hits"]["hits"]:
            (id, title, description, downloads) = self.parse_basic_info(hit)
            author = hit["metadata"]["creators"][0]["name"]
            publication_date = hit["metadata"]['publication_date']
            doi = hit["doi"]
            keyword_data = self.get_keyword_data(hit["metadata"]["keywords"])
            container = keyword_data["container-type"]
            if (searchType == "software"):
                version = hit["metadata"]["version"]
                schema_version = keyword_data["schema-version"]
            other_tags = ",".join(keyword_data["other"])
            if (searchType == "software"):
                result_dict = OrderedDict([
                    ("ID", id),
                    ("TITLE", title),
                    ("DESCRIPTION", description),
                    ("PUBLICATION DATE", publication_date),
                    ("DEPRECATED", 'deprecated' in keyword_data['other']),
                    ("DOWNLOADS", downloads),
                    ("AUTHOR", author),
                    ("VERSION", version),
                    ("DOI", doi),
                    ("SCHEMA VERSION", schema_version),
                    ("CONTAINER", container),
                    ("TAGS", other_tags)])
            else:
                result_dict = OrderedDict([
                    ("ID", id),
                    ("TITLE", title),
                    ("DESCRIPTION", description),
                    ("PUBLICATION DATE", publication_date),
                    ("DEPRECATED", 'deprecated' in keyword_data['other']),
                    ("DOWNLOADS", downloads),
                    ("AUTHOR", author),
                    ("DOI", doi),
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
        if self.max_results:
            return results_list[:self.max_results]
        else:
            return results_list

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

    def zenodo_pull(self, zids, firstKeyWord,
                    secondKeyWord, searchType, dataPull):
        # return cached file if it exists
        zenodo_entries = []
        cache_dir = os.path.join(
            os.path.expanduser('~'), ".cache", "boutiques",
            "sandbox" if self.sandbox else "production")
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
                newfname = os.path.join(cache_dir,
                                        "zenodo-{0}.json".format(newzid))
                zenodo_entries.append({"zid": newzid, "fname": newfname})
            except IndexError:
                raise_error(ZenodoError, "Zenodo ID must be prefixed by "
                                         "'zenodo', e.g. zenodo.123456")
        if (self.verbose):
            for zid in discarded_zids:
                print_info("Discarded duplicate id {0}".format(zid))
        json_files = []
        for entry in zenodo_entries:
            if os.path.isfile(entry["fname"]):
                if (self.verbose):
                    print_info("Found cached file at %s"
                               % entry["fname"])
                json_files.append(entry["fname"])
                continue

            query_line = 'AND "'+entry["zid"]+'"'
            query = ''
            r = self.zenodo_search(query, query_line, firstKeyWord,
                                   secondKeyWord, searchType)
            if not dataPull:
                if not len(r.json()["hits"]["hits"]):
                    raise_error(ZenodoError, "Descriptor \"{0}\" "
                                             "not found".format(entry["zid"]))
                for hit in r.json()["hits"]["hits"]:
                    file_path = hit["files"][0]["links"]["self"]
                    file_name = file_path.split(os.sep)[-1]
                    if hit["id"] == int(entry["zid"]):
                        if not os.path.exists(cache_dir):
                            os.makedirs(cache_dir)
                        if (self.verbose):
                            print_info("Downloading descriptor %s"
                                       % file_name)
                        downloaded = urlretrieve(file_path, entry["fname"])
                        if (self.verbose):
                            print_info("Downloaded descriptor to "
                                       + downloaded[0])
                        json_files.append(downloaded[0])
                    else:
                        raise_error(ZenodoError,
                                    "Searched-for descriptor \"{0}\""
                                    " does not match descriptor \"{1}\""
                                    " returned from Zenodo".format(
                                        entry["zid"], hit["id"]))

            else:
                if not len(r.json()["hits"]["hits"]):
                    raise_error(ZenodoError, "Execution record \"{0}\" "
                                             "not found".format(entry["zid"]))
                for hit in r.json()["hits"]["hits"]:
                    new_dir = os.path.join(cache_dir, "zenodo." + entry["zid"])
                    if not os.path.isdir(new_dir):
                        os.mkdir(new_dir)

                    for i in range(len(hit["files"])):
                        file_path = hit["files"][i]["links"]["self"]
                        file_name = file_path.split(os.sep)[-1]

                        new_filename = hit["files"][i]["key"]

                        if hit["id"] == int(entry["zid"]):
                            if not os.path.exists(cache_dir):
                                os.makedirs(cache_dir)
                            if (self.verbose):
                                print_info("Downloading execution record %s"
                                           % file_name)

                            downloaded = urlretrieve(
                                file_path,
                                os.path.join(cache_dir, "zenodo." +
                                             entry["zid"], new_filename))

                            if (self.verbose):
                                print_info("Downloaded execution record to "
                                           + downloaded[0])
                            json_files.append(downloaded[0])
                        else:
                            raise_error(ZenodoError,
                                        "Searched-for descriptor \"{0}\""
                                        " does not match descriptor \"{1}\""
                                        " returned from Zenodo".format(
                                            entry["zid"], hit["id"]))
        return json_files

    def zenodo_upload_file(self, deposition_id, file_path,
                           zenodo_access_token=None,
                           error_msg="Cannot Upload to Zenodo",
                           verbose_msg="Uploaded to Zenodo"):
        zenodo_access_token = self.get_zenodo_access_token if\
            zenodo_access_token is None else zenodo_access_token
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/files'
                          % deposition_id,
                          params={'access_token': zenodo_access_token},
                          data={'filename': os.path.basename(file_path)},
                          files={'file': open(file_path, 'rb')})

        if(r.status_code != 201):
            raise_error(ZenodoError, error_msg, r)
        if(self.verbose):
            print_info(verbose_msg, r)
