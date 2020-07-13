#!/usr/bin/env python

from boutiques.logger import print_info
from urllib.parse import quote


class Searcher():

    def __init__(self, query, verbose=False, sandbox=False, max_results=None,
                 no_trunc=False, exact_match=False):
        if query is not None:
            self.query = query
            self.query_line = ''
            if not exact_match:
                terms = self.query.replace('/', '.').split(" ")
                for t in terms:
                    uncased_term = ["[{0}]".format(ch.upper() + ch.lower()
                                                   if ch.isalpha() else ch)
                                    for ch in t]
                    uncased_term = quote("".join(uncased_term))
                    self.query_line += ' AND (/.*%s.*/)' % uncased_term
            else:
                self.query_line = ' AND (/%s/)' % self.query.replace('/', '.')
        else:
            self.query = ''
            self.query_line = ''

        if(verbose):
            print_info("Using Query Line: " + self.query_line)

        self.verbose = verbose
        self.sandbox = sandbox
        self.no_trunc = no_trunc
        self.max_results = max_results
        self.exact_match = exact_match

        # Display top 10 results by default
        if max_results is None:
            self.max_results = 10

        # Zenodo will error if asked for more than 9999 results
        if self.max_results > 9999:
            self.max_results = 9999

        # Set Zenodo endpoint
        self.zenodo_endpoint = "https://sandbox.zenodo.org" if\
            self.sandbox else "https://zenodo.org"
        if(self.verbose):
            print_info("Using Zenodo endpoint {0}".
                       format(self.zenodo_endpoint))

    def search(self):
        # Get all results
        firstKeyWord = "Boutiques"
        secondKeyWord = "schema-version.*"
        searchType = "software"
        from boutiques.zenodoHelper import ZenodoHelper
        zenodoHelper = ZenodoHelper(sandbox=self.sandbox, verbose=self.verbose,
                                    max_results=self.max_results,
                                    no_trunc=self.no_trunc)

        return zenodoHelper.search(self.query, self.query_line, firstKeyWord,
                                   secondKeyWord, searchType)
