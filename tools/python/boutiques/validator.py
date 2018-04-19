#!/usr/bin/env python

# Copyright 2015 - 2017:
#   The Royal Institution for the Advancement of Learning McGill University,
#   Centre National de la Recherche Scientifique,
#   University of Southern California,
#   Concordia University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import simplejson
import os.path as op
from jsonschema import validate, ValidationError
from argparse import ArgumentParser
from boutiques import __file__ as bfile


# An exception class specific to descriptors
class DescriptorValidationError(ValidationError):
    pass


# Main validation module
def validate_descriptor(json_file, **kwargs):
    """
    Validates the Boutiques descriptor against the schema.
    """
    path, fil = op.split(bfile)
    schema_file = op.join(path, "schema", "descriptor.schema.json")

    # Load schema
    with open(schema_file) as fhandle:
        schema = simplejson.load(fhandle)

    # Load descriptor
    with open(json_file) as fhandle:
        try:
            descriptor = simplejson.load(fhandle)
        except simplejson.errors.JSONDecodeError as e:
            raise DescriptorValidationError(str(e))

    # Validate basic JSON schema compliance for descriptor
    # Note: if it fails basic schema compliance we don"t do more checks
    try:
        validate(descriptor, schema)
    except ValidationError as e:
        raise DescriptorValidationError(str(e))

    # Helper get functions
    def safeGet(desc, sec, targ):
        return [item[targ] for item in desc[sec]
                if list(item.keys()).count(targ)]

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

    # Begin looking at Boutiques-specific failures
    errors = []

    clkeys = inputGet("value-key") + outputGet("value-key")
    flattenedTemplates = [y for x in outputGet("file-template") for y in x]
    configFileTemplates = flattenedTemplates + outputGet("path-template")

    cmdline = descriptor["command-line"]

    # Verify that all command-line key appear in the command-line
    msg_template = "   KeyError: \"{0}\" not in command-line or file template"
    errors += [msg_template.format(k)
               for k in clkeys
               if (cmdline.count(k) +
                   " ".join(configFileTemplates).count(k)) < 1]

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
    for idx, out1 in enumerate(descriptor["output-files"]):
        for jdx, out2 in enumerate(descriptor["output-files"]):
            if out1["path-template"] == out2["path-template"] and jdx > idx:
                errors += [msg_template.format(out1["id"], out2["id"])]
            else:
                errors += []

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
            if ("default-value" in inp.keys()
               and inp["default-value"] not in inp["value-choices"]):
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

        # Verify requires- and disables-inputs (present ids, non-overlapping)
        msg_template = " InputError: \"{0}\" {1}d id \"{2}\" not found"
        for param in ["require", "disable"]:
            if param+"s-inputs" in inp.keys():
                errors += [msg_template.format(inp["id"], param, ids)
                           for ids in inp[param+"s-inputs"]
                           if ids not in inIds]

        if "requires-inputs" in inp.keys() and "disables-inputs" in inp.keys():
            msg_template = " InputError: \"{0}\" requires and disables \"{1}\""
            errors += [msg_template.format(inp["id"], ids1)
                       for ids1 in inp["requires-inputs"]
                       for ids2 in inp["disables-inputs"]
                       if ids1 == ids2]

        # Verify required inputs cannot require or disable other parameters
        if "requires-inputs" in inp.keys() or "disables-inputs" in inp.keys():
            msg_template = (" InputError: \"{0}\" cannot require or"
                            " disable other inputs")
            if not inp["optional"]:
                errors += [msg_template.format(inp["id"])]

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

        for jdx, grp2 in enumerate(descriptor["groups"]):
            msg_template = (" GroupError: \"{0}\" and \"{1}\" both contain"
                            " member \"{2}\"")
            errors += [msg_template.format(grp["id"], grp2["id"], m1)
                       for m1 in grp["members"]
                       for m2 in grp2["members"]
                       if m1 == m2 and idx > jdx]

        # Verify mutually exclusive groups cannot have required members
        # nor requiring members
        if "mutually-exclusive" in grp.keys():
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

        # Verify one-is-required groups should never have required members
        if "one-is-required" in grp.keys():
            msg_template = (" GroupError: \"{0}\" is a one-is-required"
                            " group and contains a required member, \"{1}\"")
            errors += [msg_template.format(grp["id"], member)
                       for member in set(grp["members"])
                       if member in inIds and not inById(member)["optional"]]

        # Verify one-is-required groups should never have required members
        if "all-or-none" in grp.keys():
            msg_template = (" GroupError: \"{0}\" is an all-or-none group"
                            " and cannot be paired with one-is-required"
                            " or mutually-exclusive groups")
            if ("one-is-required" in grp.keys()
               or "mutually-exclusive" in grp.keys()):
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
                # references refering to the same id
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

    errors = None if errors == [] else errors
    if errors is None:
        if kwargs.get("verbose"):
            print("Boutiques validation OK")
        return descriptor
    else:
        raise DescriptorValidationError("\n".join(errors))
