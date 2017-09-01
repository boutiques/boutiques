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
from boutiques import __file__


# Main validation module
def validate_json(json_file):
    """
    Validates the Boutiques descriptor against the schema.
    """
    path, fil = op.split(__file__)
    schema_file = op.join(path, "schema", "descriptor.schema.json")

    # Load schema
    with open(schema_file) as fhandle:
        schema = simplejson.load(fhandle)

    # Load descriptor
    with open(json_file) as fhandle:
        descriptor = simplejson.load(fhandle)

    # Validate basic JSON schema compliance for descriptor
    # Note: if it fails basic schema compliance we don"t do more checks
    try:
        validate(descriptor, schema)
    except ValidationError as e:
        print("JSON Validation error (Boutiques validation not yet performed)")
        raise ValidationError(e)

    # Helper get-function
    safeGet   = lambda desc, sec, targ: [item[targ] for item in desc[sec]
                                         if list(item.keys()).count(targ)]
    inputGet  = lambda s: safeGet(descriptor, "inputs", s)
    outputGet = lambda s: safeGet(descriptor, "output-files", s)
    groupGet  = lambda s: safeGet(descriptor, "groups", s)
    inById    = lambda i: descriptor["inputs"][inputGet("id").index(i)] if i in inputGet("id") else {}

    # Begin looking at Boutiques-specific failures
    errors = []

    clkeys = inputGet("value-key") + outputGet("value-key")
    configFileTemplates = outputGet("file-template") + outputGet("path-template")
    cmdline = descriptor["command-line"]

    # Verify that all command-line key appear in the command-line
    msg_template = "   KeyError: \"{}\" not in command-line or file template"
    errors += [msg_template.format(k)
               for k in clkeys
               if (cmdline.count(k) + " ".join(configFileTemplates).count(k)) < 1]

    # Verify that no key contains another key
    msg_template = "   KeyError: \"{}\" contains \"{}\""
    errors += [msg_template.format(key, clkeys[jdx])
               for idx, key in enumerate(clkeys)
               for jdx in range(0, len(clkeys))
               if clkeys[jdx] in key and key != clkeys[jdx]]

    # Verify that all Ids are unique
    inIds, outIds = inputGet("id"), outputGet("id")
    grpIds = groupGet("id") if "groups" in descriptor.keys() else []
    allIds = inIds + outIds + grpIds
    msg_template = "    IdError: \"{}\" is non-unique"
    for idx, s1 in enumerate(allIds):
        for jdx, s2 in enumerate(allIds):
            errors += [msg_template.format(s1)] if s1 == s2 and idx < jdx else []

    # Verify that identical keys only exist if they are both in mutex groups
    msg_template = " MutExError: \"{}\" belongs to 2+ non exclusive IDs"
    for idx, key in enumerate(clkeys):
        for jdx in range(idx+1, len(clkeys)):
            if clkeys[jdx] == key:
                mids = [inById(mid)["id"] for mid in inIds
                        if inById(mid)["value-key"] == key]
                for idx, grp in enumerate(descriptor["groups"]):
                    mutex = grp.get("mutually-exclusive")
                    if set(grp["members"]) == set(mids) and not mutex:
                        errors += [msg_template.format(key)]

    # Verify that output files have unique path-templates
    msg_template = "OutputError: \"{}\" and \"{}\" have the same path-template"
    for idx, out1 in enumerate(descriptor["output-files"]):
        for jdx, out2 in enumerate(descriptor["output-files"]):
            errors += [msg_template.format(out1["id"], out2["id"])] if out1["path-template"] == out2["path-template"] and jdx > idx else []

    # Verify inputs
    for inp in descriptor["inputs"]:

        # Add optional property in case it's not there (default to false as in JSON)
        if "optional" not in inp.keys():
            inp["optional"] = False
        
        # Verify flag-type inputs (have flags, not required, cannot be lists)
        if inp["type"] == "Flag":
            msg_template = " InputError: \"{}\" must have a command-line flag"
            errors += [msg_template.format(inp["id"])] if "command-line-flag" not in inp.keys() else []

            msg_template = " InputError: \"{}\" should not be required"
            errors += [msg_template.format(inp["id"])] if inp["optional"] is False else []

        # Verify number-type inputs min/max are sensible
        elif inp["type"] == "Number":
            msg_template = " InputError: \"{}\" cannot have greater min ({}) than max ({})"
            minn = inp["minimum"] if "minimum" in inp.keys() else -float("Inf")
            maxx = inp["maximum"] if "maximum" in inp.keys() else float("Inf")
            errors += [msg_template.format(inp["id"], minn, maxx)] if minn > maxx else []

        # Verify enum-type inputs (at least 1 option, default in set)
        elif "value-choices" in inp.keys():
            msg_template = " InputError: \"{}\" must have at least one value choice"
            errors += [msg_template.format(inp["id"])] if len(inp["value-choices"]) < 1 else []

            msg_template = " InputError: \"{}\" cannot have default value outside its choices"
            errors += [msg_template.format(inp["id"])] if "default-value" in inp.keys() and inp["default-value"] not in inp["value-choices"] else []

        # Verify list-type inputs (min entries less than max, no negative entries (both on min and max)
        if "list" in inp.keys():
            msg_template = " InputError: \"{}\" cannot have greater min entries ({}) than max entries ({})"
            minn = inp["min-list-entries"] if "min-list-entries" in inp.keys() else 0
            maxx = inp["max-list-entries"] if "max-list-entries" in inp.keys() else float("Inf")
            errors += [msg_template.format(inp["id"], minn, maxx)] if minn > maxx else []

            msg_template = " InputError: \"{}\" cannot have negative min entries ({})"
            errors += [msg_template.format(inp["id"], minn)] if minn < 0 else []

            msg_template = " InputError: \"{}\" cannot have non-positive max entries ({})"
            errors += [msg_template.format(inp["id"], maxx)] if maxx <= 0 else []

        # Verify requires- and disables-inputs (present ids, non-overlapping)
        msg_template = " InputError: \"{}\" {}d id \"{}\" not found"
        for param in ["require", "disable"]:
            if param+"s-inputs" in inp.keys():
                errors += [msg_template.format(inp["id"], param, ids)
                           for ids in inp[param+"s-inputs"]
                           if ids not in inIds]

        if "requires-inputs" in inp.keys() and "disables-inputs" in inp.keys():
            msg_template = " InputError: \"{}\" requires and disables \"{}\""
            errors += [msg_template.format(inp["id"], ids1)
                       for ids1 in inp["requires-inputs"]
                       for ids2 in inp["disables-inputs"]
                       if ids1 == ids2]

        # Verify required inputs cannot require or disable other parameters
        if "requires-inputs" in inp.keys() or "disables-inputs" in inp.keys():
            msg_template = " InputError: \"{}\" cannot require or disable other inputs"
            if not inp["optional"]:
                errors += [msg_template.format(inp["id"])]

    # Verify groups
    for idx, grpid in enumerate(grpIds):
        grp = descriptor['groups'][idx]
        # Verify group members must (exist in inputs, show up once, only belong to single group)
        msg_template = " GroupError: \"{}\" member \"{}\" does not exist"
        errors += [msg_template.format(grp["id"], member)
                   for member in grp["members"] if member not in inIds]

        msg_template = " GroupError: \"{}\" member \"{}\" appears twice"
        errors += [msg_template.format(grp["id"], member)
                   for member in set(grp["members"])
                   if grp["members"].count(member) > 1]

        for jdx, grp2 in enumerate(descriptor["groups"]):
            msg_template = " GroupError: \"{}\" and \"{}\" both contain member \"{}\""
            errors += [msg_template.format(grp["id"], grp2["id"], m1)
                       for m1 in grp["members"]
                       for m2 in grp2["members"]
                       if m1 == m2 and idx > jdx]

        # Verify mutually exclusive groups cannot have required members nor requiring members
        if "mutually-exclusive" in grp.keys():
            msg_template = " GroupError: \"{}\" is mutually-exclusive and cannot have required members, such as \"{}\""
            errors += [msg_template.format(grp["id"], member)
                       for member in set(grp["members"]) if not inById(member)["optional"]]

            msg_template = " GroupError: \"{}\" is mutually-exclusive and cannot have members require one another, such as \"{}\" and \"{}\""
            for member in set(grp["members"]):
                if "requires-inputs" in inById(member).keys():
                    errors += [msg_template.format(grp["id"], member, req)
                               for req in inById(member)["requires-inputs"]
                               if req in set(grp["members"])]

        # Verify one-is-required groups should never have required members
        if "one-is-required" in grp.keys():
            msg_template = " GroupError: \"{}\" is a one-is-required group and contains a required member, \"{}\""
            errors += [msg_template.format(grp["id"], member)
                       for member in set(grp["members"])
                       if member in inIds and not inById(member)["optional"]]

        # Verify one-is-required groups should never have required members
        if "all-or-none" in grp.keys():
            msg_template = " GroupError: \"{}\" is an all-or-none group and cannot be paired with one-is-required or mutually-exclusive groups"
            if "one-is-required" in grp.keys() or "mutually-exclusive" in grp.keys():
                errors += [msg_template.format(grp["id"])]

            msg_template = " GroupError: \"{}\" is an all-or-none group and contains a required member, \"{}\""
            errors += [msg_template.format(grp["id"], member)
                       for member in set(grp["members"])
                       if member in inIds and not inById(member)["optional"]]

    errors = None if errors == [] else errors
    if errors is None:
        print("Boutiques validation OK")
        return descriptor
    else:
        raise ValidationError("Invalid descriptor:\n"+"\n".join(errors))


def main(args=None):
    parser = ArgumentParser("Boutiques Validator")
    parser.add_argument("jsonfile", action="store",
                        help="The Boutiques descriptor you wish to validate")
    parser.add_argument("--bids", "-b", action="store_true",
                        help="Flag indicating if descriptor is for a BIDS app")
    results = parser.parse_args() if args is None else parser.parse_args(args)

    descriptor = validate_json(results.jsonfile)

    if results.bids:
        from boutiques.bids import validate_bids
        validate_bids(descriptor, valid=True)
        return 0

if __name__ == "__main__":
    main()
