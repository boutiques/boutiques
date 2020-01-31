import os
import simplejson as json
from boutiques.logger import raise_error
from boutiques import __file__ as bfile


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
def loadJson(userInput, verbose=False):
    # Check for JSON file (local or from Zenodo)
    json_file = None
    if os.path.isfile(userInput):
        json_file = userInput
    elif userInput.split(".")[0].lower() == "zenodo":
        from boutiques.puller import Puller
        puller = Puller([userInput], verbose)
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


# Recursively sorts and returns a descriptor dictionary according to
# the keys' order in a template descriptor
def customSortDescriptorByKey(descriptor,
                              template=os.path.join(
                                  os.path.dirname(bfile),
                                  "templates",
                                  "ordered_keys_desc.json")):

    def sortListedObjects(objList, template):
        sortedObjList = []
        for obj in objList:
            sortedObj = {key: obj[key] for key in template if
                         key in obj}
            sortedObj.update(obj)
            sortedObjList.append(sortedObj)

        # Safety: return original if sortedObjList is faulty
        try:
            for obj, sobj in zip(objList, sortedObjList):
                if obj != sobj:
                    sortedObjList = objList
                    break
        except Exception:
            print("[ERROR] Sorted list does not represent original list.")
            return objList
        return sortedObjList

    template = loadJson(template)
    sortedDesc = {}
    # Add k:v to sortedDesc according to their order in template
    for key in [k for k in template if k in descriptor]:
        if type(descriptor[key]) is list:
            sortedDesc[key] =\
                sortListedObjects(descriptor[key], template[key][0])
        else:
            sortedDesc[key] = descriptor[key]

    # Add remaining k:v that are missing from template
    sortedDesc.update(descriptor)
    if sortedDesc != descriptor:
        return descriptor
    return sortedDesc


# Recursively sorts tool invocations according to descriptor's inputs'
def customSortInvocationByInput(invocation, descriptor):
    descriptor = loadJson(descriptor)
    try:
        # sort invoc according to input's order in decsriptor
        sortedInvoc = {key: invocation[key] for key in
                       [inp['id'] for inp in descriptor['inputs']
                        if descriptor['inputs'] is not None]
                       if key in invocation}
        if sortedInvoc != invocation:
            return invocation
    except Exception:
        print("[ERROR] Sorted invocation does not"
              " represent original invocation")
        return invocation
    return sortedInvoc
