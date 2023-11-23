import os
import simplejson as json
from collections import OrderedDict
from boutiques.logger import raise_error, print_warning
from boutiques import __file__ as bfile


# Utility function to wrap modules that use non-essential libs
def importCatcher():
  def decorate(f):
    def applicator(*args, **kwargs):
      try:
         return f(*args,**kwargs)
      except ImportError as e:
         print(e)
         raise ImportError("Try installing the full version of Boutiques "
                           "with: \n\t pip install -e boutiques[all]")

    return applicator
  return decorate


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
    elif "zenodo" in ".".join(userInput.split('.')[:-1]).lower():
        from boutiques.puller import Puller
        puller = Puller([userInput], verbose, sandbox)
        json_file = puller.pull()[0]
    if json_file is not None:
        with open(json_file, 'r') as f:
            return OrderedDict(json.loads(f.read(),
                                          object_pairs_hook=OrderedDict))
    # JSON file not found, so try to parse JSON object
    e = ("Cannot parse input {}: file not found, "
         "invalid Zenodo ID, or invalid JSON object").format(userInput)
    if userInput.isdigit():
        raise_error(LoadError, e)
    try:
        return OrderedDict(json.loads(userInput,
                                      object_pairs_hook=OrderedDict))
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


# Sorts and returns a descriptor dictionary according to
# the keys' order in a template descriptor
def customSortDescriptorByKey(descriptor,
                              template=os.path.join(
                                  os.path.dirname(bfile),
                                  "templates",
                                  "ordered_keys_desc.json")):

    def sortListedObjects(objList, template):
        sortedObjList = []
        for obj in objList:
            sortedObj = OrderedDict()
            for key in template:
                if key in obj:
                    sortedObj[key] = obj[key]
            for key in obj:
                if key not in template:
                    sortedObj[key] = obj[key]
            sortedObjList.append(sortedObj)

        if len(objList) != len(sortedObjList):
            print_warning("Sorted list does not represent"
                          " original list.")
            return objList
        for obj, sobj in zip(objList, sortedObjList):
            if obj != dict(sobj):
                print_warning("Sorted list does not represent"
                              " original list.")
                return objList
        return sortedObjList

    template = loadJson(template)
    sortedDesc = OrderedDict()

    # Add k:v to sortedDesc according to their order in template
    for key in template:
        if key in descriptor:
            if type(descriptor[key]) is list:
                sortedDesc[key] =\
                    sortListedObjects(descriptor[key], template[key][0])
            elif type(descriptor[key]) is dict:
                sortedDesc[key] = customSortDescriptorByKey(
                    descriptor[key], template=json.dumps(template[key]))
            else:
                sortedDesc[key] = descriptor[key]

    # Add remaining k:v that are missing from template
    for key in descriptor:
        if key not in sortedDesc:
            sortedDesc[key] = descriptor[key]
    if sortedDesc != descriptor:
        print_warning("Sorted descriptor does not represent"
                      " original descriptor.")
        return descriptor
    return sortedDesc


# Sorts tool invocations according to descriptor's inputs'
def customSortInvocationByInput(invocation, descriptor):
    descriptor = loadJson(descriptor)
    # sort invoc according to input's order in descriptor
    sortedInvoc = OrderedDict()
    sortedInvoc.update({key: invocation[key] for key in
                        [inp['id'] for inp in descriptor['inputs']
                            if descriptor['inputs'] is not None]
                        if key in invocation})
    if sortedInvoc != invocation:
        print_warning("Sorted invocation does not represent"
                      " original invocation.")
        return invocation
    return sortedInvoc


def snakeCaseToCamelCase(id):
    words = id.split("_")
    for idx, word in enumerate(words[1:]):
        if word[0].islower():
            words[idx+1] = word[0].upper() + word[1:]
    return "".join(words)


def camelCaseInputIds(descriptor):
    conversion_dict = {}
    if 'inputs' in descriptor:
        for inp in descriptor['inputs']:
            camelCaseId = snakeCaseToCamelCase(inp['id'])
            conversion_dict[inp['id']] = camelCaseId

    # Find all instances of old input ids
    # and replace them with camelCase ids
    plainTextDesc = json.dumps(descriptor, indent=2)
    for k, v in conversion_dict.items():
        # Only replace ids surrounded by single/double quotes,
        # in case the the old input ids are used in other strings
        plainTextDesc = plainTextDesc.replace("\"{0}\"".format(k),
                                              "\"{0}\"".format(v))
        plainTextDesc = plainTextDesc.replace("\'{0}\'".format(k),
                                              "\'{0}\'".format(v))
    descriptor = json.loads(plainTextDesc)
    return descriptor


def formatSphinxUsage(func, usage_str):
    args = usage_str.replace("[", " ")\
        .replace("]", " ")\
        .replace("\n", "")\
        .split(func)[1:]
    args = "".join(args)
    args = args.split("  ")[0:]
    args = list(filter(lambda x: x != "", args))
    args = ["\"{}\"".format(arg.strip()) for arg in args]
    args = ", ".join(args)
    return "[{}]".format(args)
