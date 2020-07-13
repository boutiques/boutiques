from boutiques.zenodoHelper import ZenodoError


class Puller():

    def __init__(self, zids, verbose=False, sandbox=False):
        self.verbose = verbose
        self.sandbox = sandbox
        self.zids = zids

    def pull(self):
        dataPull = False
        firstKeyWord = "Boutiques"
        secondKeyWord = "schema-version.*"
        searchType = "software"
        from boutiques.zenodoHelper import ZenodoHelper
        zenodoHelper = ZenodoHelper(verbose=self.verbose, sandbox=self.sandbox)

        return zenodoHelper.zenodo_pull(self.zids, firstKeyWord,
                                        secondKeyWord, searchType, dataPull)
