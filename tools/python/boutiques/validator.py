#!/usr/bin/env python
#
# Copyright (C) 2015
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
import simplejson
import os.path as op
import numpy as np
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
        print("Error: {}".format(e))
        return -1

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
    errors += [msg_template.format(k.strip("[]"))
               for k in clkeys
               if (cmdline.count(k) + " ".join(configFileTemplates).count(k)) < 1]

    # Verify that no key contains another key
    msg_template = "   KeyError: \"{}\" contains \"{}\""
    errors += [msg_template.format(key.strip("[]"), clkeys[jdx].strip("[]"))
               for idx, key in enumerate(clkeys)
               for jdx in range(0, len(clkeys))
               if clkeys[jdx].strip("[]") in key and key is not clkeys[jdx]]

    # Verify that all Ids are unique
    inIds, outIds, grpIds = inputGet("id"), outputGet("id"), groupGet("id")
    allIds = inIds + outIds + grpIds
    msg_template = "    IdError: \"{}\" is non-unique"
    for idx, s1 in enumerate(allIds):
        for jdx, s2 in enumerate(allIds):
            errors += [msg_template.format(s1)] if s1 == s2 and idx < jdx else []

    # Verify that output files have unique path-templates
    msg_template = "OutputError: \"{}\" and \"{}\" have the same path-template"
    for idx, out1 in enumerate(descriptor["output-files"]):
        for jdx, out2 in enumerate(descriptor["output-files"]):
            errors += [msg_template.format(out1["id"], out2["id"])] if out1["path-template"] == out2["path-template"] and jdx > idx else []

    # Verify inputs
    for inp in descriptor["inputs"]:

        # Verify flag-type inputs (have flags, not required, cannot be lists)
        if inp["type"] == "Flag":
            msg_template = " InputError: \"{}\" must have a command-line flag"
            errors += [msg_template.format(inp["id"])] if "command-line-flag" not in inp.keys() else []

            msg_template = " InputError: \"{}\" should not be required"
            errors += [msg_template.format(inp["id"])] if inp["optional"] is False else []

            # This one is redundant as basic JSON validation catches it
            msg_template = " InputError: \"{}\" cannot be a list"
            errors += [msg_template.format(inp["id"])] if "list" in inp.keys() else []

        # Verify number-type inputs min/max are sensible
        elif inp["type"] == "Number":
            msg_template = " InputError: \"{}\" cannot have greater min ({}) than max ({})"
            minn = inp["minimum"] if "minimum" in inp.keys() else -np.inf
            maxx = inp["maximum"] if "maximum" in inp.keys() else np.inf
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
            maxx = inp["max-list-entries"] if "max-list-entries" in inp.keys() else np.inf
            errors += [msg_template.format(inp["id"], minn, maxx)] if minn > maxx else []

            msg_template = " InputError: \"{}\" cannot have negative min entries ({})"
            errors += [msg_template.format(inp["id"], minn)] if minn < 0 else []

            msg_template = " InputError: \"{}\" cannot have non-positive max entries ({})"
            errors += [msg_template.format(inp["id"], maxx)] if maxx <= 0 else []

        # Verify non list-type inputs don"t have list properties
        # This one is redundant as basic JSON validation catches it
        else:
            msg_template = " InputError: \"{}\" cannot use min- or max-list-entries"
            errors += [msg_template.format(inp["id"])] if "min-list-entries" in inp.keys() or "max-list-entries" in inp.keys() else []

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
    for idx, grp in enumerate(descriptor["groups"]):

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

    errors = ["OK"] if errors == [] else errors
    print("\n".join(errors))


def main():
    parser = ArgumentParser("Boutiques Validator")
    parser.add_argument("json_file", action="store", nargs="1",
                        help="The Boutiques descriptor you wish to validate")
    json_file = parser.parse_args()["json_file"]
    validate_json(json_file)


if __name__ == "__main__":
    main()
