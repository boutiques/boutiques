import os
import simplejson as json
from boutiques.logger import raise_error


# Parses absolute path into filename
def extractFileName(path):
    # Helps OS path handle case where "/" is at the end of path
    if path is None:
        return None
    elif path[:-1] == '/':
        return os.path.basename(path[:-1]) + "/"
    else:
        return os.path.basename(path)


class LoadError(Exception):
    pass


# Helper function that loads the JSON object coming from either a string,
# a local file or a file pulled from Zenodo
def loadJson(userInput, verbose=False, sandbox=False):
    # Check for JSON file (local or from Zenodo)
    json_file = None
    if os.path.isfile(userInput):
        json_file = userInput
    elif userInput.split(".")[0].lower() == "zenodo":
        from boutiques.puller import Puller
        puller = Puller([userInput], verbose, sandbox)
        json_file = puller.pull()[0]
    if json_file is not None:
        with open(json_file, 'r') as f:
            return json.loads(f.read())
    # JSON file not found, so try to parse JSON object
    e = ("Cannot parse input {}: file not found, "
         "invalid Zenodo ID, or invalid JSON object").format(userInput)
    if userInput.isdigit():
        raise_error(LoadError, e)
    try:
        return json.loads(userInput)
    except ValueError:
        raise_error(LoadError, e)


# Helper function that takes a conditional path template key as input,
# and outputs a formatted string that isolates variables/values from
# operators, parentheses, and python keywords with a space.
# ex: "(opt1>2)" becomes " ( opt1 > 2 ) "
# "(opt1<=10.1)" becomes " ( opt1 <= 10.1 ) "
def conditionalExpFormat(s):
    cleanedExpression = ""
    idx = 0
    while idx < len(s):
        c = s[idx]
        if c in ['=', '!', '<', '>']:
            cleanedExpression += " {0}{1}".format(
                c, "=" if s[idx+1] == "=" else " ")
            idx += 1
        elif c in ['(', ')']:
            cleanedExpression += " {0} ".format(c)
        else:
            cleanedExpression += c
        idx += 1
    return cleanedExpression
