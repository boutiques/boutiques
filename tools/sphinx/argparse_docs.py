import simplejson as json
import subprocess
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

    # Start CLI docs .rst files creation
    indexTemplate = readFile("./_templates/index.rst")
    boshTemplate = readFile("./_templates/bosh.rst")
    # Split readme into two, slicing at command line api section
    readmeText = readFile("../python/README.rst")

    indexDocString = readmeText + "\n" + indexTemplate + "\n"

    # Create a RST page per api
    createDocsPage("bosh.rst", boshTemplate)
    createDocsPage("index.rst", indexDocString)


CreateBoshDocs()
subprocess.Popen(["make", "clean"], cwd="./").wait()
make = subprocess.Popen(["make", "html"], cwd="./").wait()
