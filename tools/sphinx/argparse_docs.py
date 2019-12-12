import simplejson as json
import boutiques


def CreateBoshDocs():
    # Get file as plain text
    def readFile(path):
        with open(path, "r") as file:
            return file.read()

    # create an RST index page
    def createDocsPage(path, docString):
        with open(path, "w+") as page:
            page.write(docString)

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

    def getPyApiTextByName(api):
        import subprocess
        apiProcess = subprocess.Popen(
            "bosh {0} -h".format(api), shell=True, stdout=subprocess.PIPE)
        output = apiProcess.stdout.read()
        return output.decode()

    # Start CLI docs .rst files creation
    boshFileText = readFile("../python/boutiques/bosh.py")
    indexTemplate = readFile("./_templates/index.rst")
    # Split readme into two, slicing at command line api section
    readmeText = readFile("../python/README.rst").split(
        "Let’s consider a few common use-cases…")
    apiNames = GenerateApiTree(boshFileText)

    indexDocString = readmeText[0] + "\n" + indexTemplate + "\n"
    for api in sorted(apiNames):
        # Add api reference to index doc string
        indexDocString += '    _{0}\n'.format(api)
        # Define Python API docs
        docString = 'Python API\n{0}\n'.format('='*len("Python API"))
        pythonAPIText = getPyApiTextByName(api)
        docString += '{0}\n'.format(pythonAPIText)
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
        createDocsPage("_{0}.rst".format(api), docString)
    # Create index RST page
    indexDocString += readmeText[1]
    createDocsPage("index.rst", indexDocString)


CreateBoshDocs()
