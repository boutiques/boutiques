#!/usr/bin/env python

import re
import keyword
import os.path as op
import simplejson as json
from jsonschema import validate, ValidationError
from argparse import ArgumentParser
from boutiques import __file__ as bfile
from boutiques.util.utils import loadJson, conditionalExpFormat
from boutiques.util.utils import customSortDescriptorByKey
from boutiques.logger import raise_error, print_info


# An exception class specific to descriptors
class DescriptorValidationError(ValidationError):
    pass


# Main validation module
def validate_descriptor(descriptor, **kwargs):
    """
    Validates the Boutiques descriptor against the schema.
    """
    path, fil = op.split(bfile)
    schema_file = op.join(path, "schema", "descriptor.schema.json")

    # Load schema
    with open(schema_file) as fhandle:
        schema = json.load(fhandle)

    # Load input types according to the schema
    schema_types = schema['properties']['inputs'][
        'items']['properties']['type']['enum']
    allowed_keywords = ['and', 'or', 'false', 'true']
    allowed_comparators = ['==', '!=', '<', '>', '<=', '>=']

    # Validate basic JSON schema compliance for descriptor
    # Note: if it fails basic schema compliance we don"t do more checks
    try:
        validate(descriptor, schema)
    except ValidationError as e:
        raise_error(DescriptorValidationError, (str(e)))

    # Helper get functions
    def safeGet(desc, sec, targ):
        if desc.get(sec):
            return [item.get(targ) for item in desc[sec]
                    if list(item.keys()).count(targ)]
        return []

    def inputGet(s):
        return safeGet(descriptor, "inputs", s)

    def outputGet(s):
        return safeGet(descriptor, "output-files", s)

    def groupGet(s):
        return safeGet(descriptor, "groups", s)

    def inById(i):
        if i in inputGet("id"):
            return descriptor["inputs"][inputGet("id").index(i)]
        return {}

    def isValidConditionalExp(exp):
        # Return the type of a conditional expression's substring
        def getSubstringType(s):
            s = s.strip()
            if s in schema_types:
                # Can't realistically distinguish File from String
                return s if s != "File" else "String"
            elif re.search(r'^[0-9]*\.?[0-9]+$', s):
                return "Number"
            elif re.search(r'^(True|False|false|true)$', s):
                return "Flag"
            else:
                return "String"

        # Recursively check boolean expression by replacing variables with
        # their expected value type [Number, String, File, Flag]
        brackets, startIdx, endIdx = 0, 0, 0
        rebuiltExp = ""
        for idx, c in enumerate(exp):
            if c == '(':
                brackets += 1
                startIdx = idx + 1
            elif c == ')':
                brackets -= 1
                if brackets == 0:
                    endIdx = idx
                    isValidSubExp = isValidConditionalExp(exp[startIdx:endIdx])
                    # Immediately return false if sub expression is not valid
                    if not isValidSubExp:
                        return False
                    else:
                        rebuiltExp += "{0}".format(isValidSubExp)
            elif brackets == 0:
                rebuiltExp += "{0}".format(c)
        rebuiltExp = rebuiltExp.strip()

        # If there are no more parentheses, check if sub-expression is valid
        # rebuiltExp should only be two values separated by operator: x >= y
        # or values separated by 'AND'/'OR': x and y and z
        if '(' not in rebuiltExp and ')' not in rebuiltExp:
            expElements = rebuiltExp.split()
            for idx, e in enumerate(expElements):
                e = e.strip()
                # Compare types of elements neighbouring allowed_comparators
                if e in allowed_comparators and\
                   getSubstringType(expElements[idx-1]) !=\
                   getSubstringType(expElements[idx+1]):
                    return False
                # Check if keyword element is part of allowed keywords
                if keyword.iskeyword(e) and e.lower() not in allowed_keywords:
                    return False
                # Check elements neighbouring and/or keywords are valid words
                if e.lower() in ["and", "or"] and (
                   expElements[idx-1] not in schema_types + ["True", "False"]
                   or
                   expElements[idx+1] not in schema_types + ["True", "False"]):
                    return False
        return True

    # Begin looking at Boutiques-specific failures
    errors = []

    clkeys = inputGet("value-key") + outputGet("value-key")
    flattenedTemplates = [y for x in outputGet("file-template") for y in x]
    configFileTemplates = flattenedTemplates + outputGet("path-template")

    cmdline = descriptor["command-line"]

    # Verify that all command-line key appear in the command-line, in
    # a file template or in an environment variable value
    msg_template = ("   KeyError: \"{0}\" not in command-line or file template"
                    " or environment variables")
    envValues = ""
    if descriptor.get('environment-variables'):
        for env in descriptor.get('environment-variables'):
            envValues += "||"+env['value']
    errors += [msg_template.format(k)
               for k in clkeys
               if ((cmdline +
                    ".".join(configFileTemplates) +
                    envValues).count(k)) < 1]

    # Verify that no key contains another key
    msg_template = "   KeyError: \"{0}\" contains \"{1}\""
    errors += [msg_template.format(key, clkeys[jdx])
               for idx, key in enumerate(clkeys)
               for jdx in range(0, len(clkeys))
               if clkeys[jdx] in key and key != clkeys[jdx]]

    # Verify that all Ids are unique
    inIds, outIds = inputGet("id"), outputGet("id")
    grpIds = groupGet("id") if "groups" in descriptor.keys() else []
    allIds = inIds + outIds + grpIds
    msg_template = "    IdError: \"{0}\" is non-unique"
    for idx, s1 in enumerate(allIds):
        for jdx, s2 in enumerate(allIds):
            if s1 == s2 and idx < jdx:
                errors += [msg_template.format(s1)]
            else:
                errors += []

    # Verify that identical keys only exist if they are both in mutex groups
    msg_template = " MutExError: \"{0}\" belongs to 2+ non exclusive IDs"
    for idx, key in enumerate(clkeys):
        for jdx in range(idx+1, len(clkeys)):
            if clkeys[jdx] == key:
                mids = [inById(mid)["id"] for mid in inIds
                        if inById(mid)["value-key"] == key]
                for idx, grp in enumerate(descriptor.get("groups")):
                    mutex = grp.get("mutually-exclusive")
                    if set(grp["members"]) == set(mids) and not mutex:
                        errors += [msg_template.format(key)]

    # Verify that output files have unique path-templates
    msg_template = ("OutputError: \"{0}\" and \"{1}\" have the same "
                    "path-template")
    for ix, o1 in zip(outputGet("id"), outputGet("path-template")):
        for jx, o2 in zip(outputGet("id"), outputGet("path-template")):
            if o1 == o2 and jx != ix:
                errors += [msg_template.format(ix, jx)]
            else:
                errors += []

    if 'output-files' in descriptor:
        # Verify output file with non-optional conditional file template
        # contains a default path
        msg_template = ("OutputError: \"{0}\". Non-optional output-file with "
                        "conditional-path-template must contain "
                        "\"default\" path-template.")

        cond_outfiles_keys = []
        for outF in [o for o in descriptor["output-files"] if
                     'conditional-path-template' in o and not o['optional']]:
            out_keys = [list(obj.keys())[0] for obj in
                        outF['conditional-path-template']]
            cond_outfiles_keys.extend(out_keys)
            if 'default' not in out_keys:
                errors += [msg_template.format(outF['id'])]

            # Verify output keys contain only one default condition
            if out_keys.count('default') > 1:
                errors += ["OutputError: \"{0}\". Only one \"default\" "
                           "condition is permitted in a "
                           "conditional-path-template.".format(outF['id'])]

        # Verify output key contains variables that correspond to input IDs
        # or is 'default'
        msg_template = ("OutputError: \"{0}\" contains non-python keyword and "
                        "non-ID string: \"{1}\"")
        for templateKey in cond_outfiles_keys:
            splitExp = conditionalExpFormat(templateKey).split()
            if splitExp[0] == 'default' and len(splitExp) == 1:
                continue
            for s in [s for s in splitExp if not keyword.iskeyword(s) and
                      s.isalnum() and not s.isdigit() and
                      s not in [i['id'] for i in descriptor['inputs']] and
                      s not in [i['id'] for i in descriptor['output-files']]]:
                errors += [msg_template.format(outF['id'], s)]

        # Verify variable is being evaluated against a value of the same type
        msg_template = ("OutputError: Conditional output \"{0}\" contains "
                        "invalid conditional expression. Verify arguments' "
                        "type and allowed keywords in expression.")
        for templateKey in cond_outfiles_keys:
            splitExp = conditionalExpFormat(templateKey).split()
            if splitExp[0] == 'default' and len(splitExp) == 1:
                continue
            # Replace variable by it's type according to the descriptor schema
            for s in [s for s in enumerate(splitExp) if
                      not keyword.iskeyword(s[1]) and
                      s[1].isalnum() and not s[1].isdigit()]:
                if s[1] in [i['id'] for i in descriptor['inputs']]:
                    splitExp[s[0]] = inById(s[1])['type']
            # Check if the conditional expression is valid
            if not isValidConditionalExp(" ".join(splitExp)):
                errors += [msg_template.format(templateKey)]

    # Verify inputs
    for inp in descriptor["inputs"]:

        # Add optional property in case it's not
        # there (default to false as in JSON)
        if "optional" not in inp.keys():
            inp["optional"] = False

        # Verify flag-type inputs (have flags, not required, cannot be lists)
        if inp["type"] == "Flag":
            msg_template = " InputError: \"{0}\" must have a command-line flag"
            if "command-line-flag" not in inp.keys():
                errors += [msg_template.format(inp["id"])]
            else:
                errors += []

            msg_template = " InputError: \"{0}\" is of type Flag,"\
                           " it has to be optional"
            if inp["optional"] is False:
                errors += [msg_template.format(inp["id"])]
            else:
                errors += []

        # Verify number-type inputs min/max are sensible
        elif inp["type"] == "Number":
            msg_template = (" InputError: \"{0}\" cannot have greater"
                            " min ({1}) than max ({2})")
            minn = inp["minimum"] if "minimum" in inp.keys() else -float("Inf")
            maxx = inp["maximum"] if "maximum" in inp.keys() else float("Inf")
            if minn > maxx:
                errors += [msg_template.format(inp["id"], minn, maxx)]
            else:
                errors += []

        # Verify enum-type inputs (at least 1 option, default in set)
        elif "value-choices" in inp.keys():
            msg_template = (" InputError: \"{0}\" must have at least"
                            " one value choice")
            if len(inp["value-choices"]) < 1:
                errors += [msg_template.format(inp["id"])]
            else:
                errors += []

            msg_template = " InputError: \"{0}\" cannot have default"\
                           " value outside its choices"
            if "default-value" in inp.keys():
                if not isinstance(inp["default-value"], list):
                    if inp["default-value"] not in inp["value-choices"]:
                        errors += [msg_template.format(inp["id"])]
                else:
                    for dv in inp["default-value"]:
                        if dv not in inp["value-choices"]:
                            errors += [msg_template.format(inp["id"])]
            else:
                errors += []

        # Verify list-type inputs (min entries less than max,
        # no negative entries (both on min and max)
        if "list" in inp.keys():
            msg_template = (" InputError: \"{0}\" cannot have greater min"
                            " entries ({1}) than max entries ({2})")
            minn = inp.get("min-list-entries") or 0
            maxx = inp.get("max-list-entries") or float("Inf")
            if minn > maxx:
                errors += [msg_template.format(inp["id"], minn, maxx)]
            else:
                errors += []

            msg_template = (" InputError: \"{0}\" cannot have negative min"
                            " entries ({1})")
            errors += [msg_template.format(inp["id"], minn)] if minn < 0 else []

            msg_template = (" InputError: \"{0}\" cannot have non-positive"
                            " max entries ({1})")
            if maxx <= 0:
                errors += [msg_template.format(inp["id"], maxx)]
            else:
                errors += []

        # Verify requires-inputs (present ids, non-overlapping)
        msg_template = " InputError: \"{0}\" required id \"{1}\" not found"
        if "requires-inputs" in inp.keys():
            errors += [msg_template.format(inp["id"], ids)
                       for ids in inp["requires-inputs"]
                       if ids not in inIds + grpIds]

        # Verify disables-inputs (present ids, non-overlapping)
        msg_template = " InputError: \"{0}\" disables id \"{1}\" not found"
        if "disables-inputs" in inp.keys():
            errors += [msg_template.format(inp["id"], ids)
                       for ids in inp["disables-inputs"]
                       if ids not in inIds]

        if "requires-inputs" in inp.keys() and "disables-inputs" in inp.keys():
            msg_template = " InputError: \"{0}\" requires and disables \"{1}\""
            errors += [msg_template.format(inp["id"], ids1)
                       for ids1 in inp["requires-inputs"]
                       for ids2 in inp["disables-inputs"]
                       if ids1 == ids2]

        # Verify that disableed inputs cannot be required
        msg_template = " InputError: \"{0}\" disables required id \"{1}\""
        if "disables-inputs" in inp.keys():
            errors += [msg_template.format(inp["id"], ids)
                       for ids in inp["disables-inputs"]
                       if ids in inIds and not inById(ids).get("optional")]


        # Verify required inputs cannot require or disable other parameters
        if "requires-inputs" in inp.keys() or "disables-inputs" in inp.keys():
            msg_template = (" InputError: \"{0}\" cannot require or"
                            " disable other inputs")
            if not inp["optional"]:
                errors += [msg_template.format(inp["id"])]

        # Verify value-disables/requires fields accompany value-choices
        if (("value-disables" in inp.keys() or
             "value-requires" in inp.keys()) and
           "value-choices" not in inp.keys()):
            msg_template = (" InputError: \"{0}\" cannot have have value-opts"
                            " without value-choices defined.")
            errors += [msg_template.format(inp["id"])]

        if "value-choices" in inp.keys():
            # Verify not value not requiring and disabling input
            if ("value-requires" in inp.keys() and
               "value-disables" in inp.keys()):
                msg_template = (" InputError: \"{0}\" choice \"{1}\" requires"
                                " and disables \"{2}\"")
                errors += [msg_template.format(inp["id"], choice, ids1)
                           for choice in inp["value-choices"]
                           for ids1 in inp["value-disables"][choice]
                           if ids1 in inp["value-requires"][choice]]

            for param in ["value-requires", "value-disables"]:
                if param in inp.keys():
                    # Verify disables/requires keys are the same as choices
                    msg_template = (" InputError: \"{0}\" {1} list is not the"
                                    " same as the value-choices")
                    if set(inp[param].keys()) != set(inp["value-choices"]):
                        errors += [msg_template.format(inp["id"], param)]

                    # Verify all required or disabled IDs are valid
                    msg_template = (" InputError: \"{0}\" {1} id \"{2}\" not"
                                    " found")
                    errors += [msg_template.format(inp["id"], param, ids)
                               for ids in inp[param].values()
                               for item in ids
                               if item not in inIds]

                    # Verify not requiring or disabling required inputs
                    msg_template = (" InputError: \"{0}\" {1} cannot be used "
                                    "with required input \"{2}\"")
                    errors += [msg_template.format(inp["id"], param, member)
                               for ids in inp[param].keys()
                               for member in inp[param][ids]
                               if not inById(member).get("optional")]

    # Verify groups
    for idx, grpid in enumerate(grpIds):
        grp = descriptor['groups'][idx]
        # Verify group members must (exist in inputs, show up
        # once, only belong to single group)
        msg_template = " GroupError: \"{0}\" member \"{1}\" does not exist"
        errors += [msg_template.format(grp["id"], member)
                   for member in grp["members"] if member not in inIds]

        msg_template = " GroupError: \"{0}\" member \"{1}\" appears twice"
        errors += [msg_template.format(grp["id"], member)
                   for member in set(grp["members"])
                   if grp["members"].count(member) > 1]

        # Verify mutually exclusive groups cannot have required members
        # nor requiring members, and that pairs of inputs cannot both be
        # in an all-or-none group
        if grp.get("mutually-exclusive"):
            msg_template = (" GroupError: \"{0}\" is mutually-exclusive"
                            " and cannot have required members, "
                            "such as \"{1}\"")
            errors += [msg_template.format(grp["id"], member)
                       for member in set(grp["members"])
                       if not inById(member)["optional"]]

            msg_template = (" GroupError: \"{0}\" is mutually-exclusive"
                            " and cannot have members require one another,"
                            " such as \"{1}\" and \"{2}\"")
            for member in set(grp["members"]):
                if "requires-inputs" in inById(member).keys():
                    errors += [msg_template.format(grp["id"], member, req)
                               for req in inById(member)["requires-inputs"]
                               if req in set(grp["members"])]

            for jdx, grp2 in enumerate(descriptor["groups"]):
                if grp2.get("all-or-none"):
                    msg_template = (" GroupError: mutually-exclusive group"
                                    " \"{0}\" and all-or-none group \"{1}\""
                                    " cannot both contain input pairs \"{2}\""
                                    " and \"{3}\"")
                    errors += [msg_template.format(grp["id"], grp2["id"],
                                                   m1, m2)
                               for m1 in grp["members"]
                               for m2 in grp["members"]
                               if m1 != m2 and m1 in grp2["members"]
                               and m2 in grp2["members"] and idx != jdx]

        # Verify one-is-required groups should never have required members
        # and that the group is not a subset of an all-or-none group
        if grp.get("one-is-required"):
            msg_template = (" GroupError: \"{0}\" is a one-is-required"
                            " group and contains a required member, \"{1}\"")
            errors += [msg_template.format(grp["id"], member)
                       for member in set(grp["members"])
                       if member in inIds and not inById(member)["optional"]]

            for jdx, grp2 in enumerate(descriptor["groups"]):
                if grp2.get("all-or-none"):
                    msg_template = (" GroupError: \"{0}\" is one-is-required"
                                    " and cannot be a subset of the all-or-none"
                                    " group \"{1}\"")
                    if (set(grp["members"]).issubset(set(grp2["members"])) and
                            idx != jdx):
                        errors += [msg_template.format(grp["id"], grp2["id"])]

        # Verify all-or-none groups should never have required members
        if grp.get("all-or-none"):
            msg_template = (" GroupError: \"{0}\" is an all-or-none group"
                            " and cannot be paired with one-is-required"
                            " or mutually-exclusive groups")
            if grp.get("one-is-required") or grp.get("mutually-exclusive"):
                errors += [msg_template.format(grp["id"])]

            msg_template = (" GroupError: \"{0}\" is an all-or-none"
                            " group and contains a required member, \"{1}\"")
            errors += [msg_template.format(grp["id"], member)
                       for member in set(grp["members"])
                       if member in inIds and not inById(member)["optional"]]

    # Verify tests
    if "tests" in descriptor.keys():
        tests_names = []
        for test in descriptor["tests"]:

            tests_names.append(test["name"])
            if "output-files" in test["assertions"].keys():
                test_output_ids = safeGet(test["assertions"],
                                          "output-files", "id")

                # Verify if output reference ids are valid
                msg_template = ("TestError: \"{0}\" output id"
                                " not found, in test \"{1}\"")
                errors += [msg_template.format(output_id, test["name"])
                           for output_id in test_output_ids
                           if (output_id not in outIds)]

                # Verify that we do not have multiple output
                # references referring to the same id
                msg_template = ("TestError: \"{0}\" output id"
                                " cannot appear more than once within"
                                " same test, in test \"{1}\"")
                errors += [msg_template.format(output_id, test["name"])
                           for output_id in set(test_output_ids)
                           if (test_output_ids.count(output_id) > 1)]

        # Verify that all the defined tests have unique names
        msg_template = "TestError: \"{0}\" test name is non-unique"
        errors += [msg_template.format(test_name)
                   for test_name in set(tests_names)
                   if (tests_names.count(test_name) > 1)]

    # Verify container image
    if "container-image" in descriptor.keys():
        conImage = descriptor['container-image']['image']
        conIndex = descriptor['container-image']['index'] if\
            'index' in descriptor['container-image'] else None
        conImageIndex = re.match(r"^[a-zA-Z0-9]+://", conImage)

        # Verify index in container image is equal to container index value
        if conIndex is not None and conImageIndex is not None and\
           conIndex != conImageIndex.group():
            msg_template = ("ContainerError: container image \"{0}\""
                            " is prepended by index that doesn't match"
                            " container index value \"{1}\"")
            errors += [msg_template.format(conImage, conIndex)]

    errors = None if errors == [] else errors
    if errors is None:
        if kwargs.get('format_output') and kwargs.get('descriptor_path'):
            with open(kwargs.get('descriptor_path'), 'w') as fhandle:
                fhandle.write(json.dumps(
                    customSortDescriptorByKey(descriptor), indent=4))
        return descriptor
    else:
        raise DescriptorValidationError("\n".join(errors))
