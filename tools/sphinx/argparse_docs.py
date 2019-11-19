import simplejson as json

boshFileText = ""
with open("../python/boutiques/bosh.py", "r") as boshFile:
    boshFileText = boshFile.read()

apiNames = {}
for scriptBlock in boshFileText.split("\n\n"):
    if scriptBlock.strip()[4:11] == "parser_":
        # take only function names starting with "def parser_" and
        # ignore the leading "def " and ending "():"
        apiFunction = scriptBlock.split('\n')[1][4:-3]
        apiName = ""
        for c in apiFunction.replace("parser_", ""):
            if c.isupper():
                apiName += (" " + c.lower())
            else:
                apiName += c

        # Create depth=2 tree if api has sub command
        # ex: "bosh": {}"bosh"
        #     "data": {  }
        if len(apiName) > 1:
            if apiName.split()[0] in apiNames:
                apiNames[apiName.split()[0]][apiName] = apiFunction
            else:
                apiNames[apiName.split()[0]] = {apiName: apiFunction}
        else:
            apiNames[apiName] = {apiName: apiFunction}

indexDocString = ''

for api in sorted(apiNames):
    indexDocString += '    {0}\n'.format(api)
    docString = ""
    for subApi in sorted(apiNames[api]):
        subDocString = '**{0}**\n'.format(subApi)
        # Only define block as module if it's not a sub-command
        headerType = "="
        if subApi != api:
            headerType = "-"
        subDocString += '{0}\n'.format(headerType*(len(subApi) + 4))
        subDocString += '''
.. argparse::
    :module: bosh
    :func: {2}
    :prog: {3}
'''.format(subApi, api, apiNames[api][subApi], subApi)
        docString += "\n" + subDocString
    with open("{0}.rst".format(api), "w+") as docPage:
        docPage.write(docString)

with open("_templates/index.rst", "r") as indexTemplate:
    with open("index.rst", "w+") as indexPage:
        indexPage.write(indexTemplate.read() + indexDocString)
