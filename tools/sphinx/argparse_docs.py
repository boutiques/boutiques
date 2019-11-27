import simplejson as json


def CreateBoshDocs():
    # Get bosh file as plain text
    def fetchBoshFile():
        with open("../python/boutiques/bosh.py", "r") as boshFile:
            return boshFile.read()

    # Get readme file as plain text
    def fetchReadMeFile():
        with open("../python/README.rst", "r") as readmeFile:
            return readmeFile.read()

    # create an RST index page
    def createDocsIndex(docString):
        with open("_templates/index.rst", "r") as indexTemplate:
            with open("index.rst", "w+") as indexPage:
                indexPage.write(indexTemplate.read() + docString)

    # create an RST API documentation page
    def createDocsPage(apiName, docString):
        with open("_{0}.rst".format(apiName), "w+") as docPage:
            docPage.write(docString)

    # Generate a structure to represent bosh APIs and subAPIs
    def GenerateApiTree(boshFileText, ):
        apiNames = {}
        for scriptBlock in boshFileText.split("\n\n"):
            if scriptBlock.strip()[4:11] == "parser_":
                # Take only function names starting with "def parser_" and
                # ignore the leading "def " and ending "():"
                apiFunction = scriptBlock.split('\n')[1][4:-3]
                apiName = ""
                for c in apiFunction.replace("parser_", ""):
                    if c.isupper():
                        apiName += (" " + c.lower())
                    else:
                        apiName += c

                # Create depth=2 tree if api has sub command
                # ex: {bosh: {bosh: parser_bosh},
                #      data: {data: parser_data,
                #             data delete: parser_dataDelete,
                #             data inspect: parser_dataInspect,
                #             data publish: parser_dataPublish}}
                if len(apiName) > 1:
                    if apiName.split()[0] in apiNames:
                        apiNames[apiName.split()[0]][apiName] =\
                            apiFunction
                    else:
                        apiNames[apiName.split()[0]] = {
                            apiName: apiFunction}
                else:
                    apiNames[apiName] = {apiName: apiFunction}
        return apiNames

    boshFileText = fetchBoshFile()
    readmeText = fetchReadMeFile()
    apiNames = GenerateApiTree(boshFileText)

    indexDocString = '\n'
    for api in sorted(apiNames):
        # Add api reference to index doc string
        indexDocString += '    _{0}\n'.format(api)
        docString = ""
        # Generate structure for each API
        for subApi in sorted(apiNames[api]):
            subDocString = '**{0}**\n'.format(subApi)
            # Define doc block title as type 1 or 2 header
            headerType = "-" if subApi != api else "="
            subDocString += '{0}\n'.format(headerType*(len(subApi) + 4))
            # Define doc block by sub-command
            subDocString += ("\n.. argparse::"
                                "\n    :module: bosh"
                                "\n    :func: {0}"
                                "\n    :prog: {1}\n").format(
                apiNames[api][subApi],
                subApi if subApi == "bosh" else "bosh " + subApi)
            docString += "\n" + subDocString
        # Create a RST page per api
        createDocsPage(api, docString)
    # Create index RST page
    createDocsIndex(indexDocString)


CreateBoshDocs()
