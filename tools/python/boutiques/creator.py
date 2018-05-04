#!/usr/bin/env python

import simplejson
import tempfile
import argparse
import sys
import os.path as op
from jsonschema import validate, ValidationError
from argparse import ArgumentParser
from boutiques import __file__ as bfile


# An exception class specific to creating descriptors.
class CreatorError(ValidationError):
    pass


class CreateDescriptor(object):
    def __init__(self, parser=None, **kwargs):
        self.descriptor = {
            "command-line": "echo [PARAM1] [PARAM2] [FLAG1] > [OUTPUT1]",
            "container-image": {
                "image": kwargs.get("container") or "user/image",
                "type": kwargs.get("container-type") or "singularity",
                "index": kwargs.get("container-index") or "docker://"
            },
            "description": kwargs.get("description") or "tool description",
            "error-codes": [
                {
                    "code": kwargs.get("error-code") or 1,
                    "description": kwargs.get("error-message") or "Crashed"
                }
            ],
            "groups": [
                {
                    "all-or-none": True,
                    "mutually-exclusive": False,
                    "one-is-required": False,
                    "id": "group1",
                    "members": [
                        "param1",
                        "flag1"
                    ],
                    "name": "the param group"
                }
            ],
            "inputs": [
                {
                    "id": "param1",
                    "name": "The first parameter",
                    "optional": True,
                    "type": "File",
                    "value-key": "[PARAM1]"
                },
                {
                    "id": "param2",
                    "name": "The second parameter",
                    "optional": False,
                    "type": "String",
                    "value-choices": [
                        "mychoice1.log",
                        "mychoice2.log"
                    ],
                    "value-key": "[PARAM2]"
                },
                {
                    "command-line-flag": "-f",
                    "id": "flag1",
                    "name": "The first flag",
                    "optional": True,
                    "type": "Flag",
                    "value-key": "[FLAG1]"
                }
            ],
            "name": kwargs.get("name") or "tool name",
            "output-files": [
                {
                    "id": "output1",
                    "name": "The first output",
                    "optional": False,
                    "value-key": "[OUTPUT1]",
                    "path-template": "[PARAM2].txt",
                    "path-template-stripped-extensions": [
                        ".log"
                    ]
                }
            ],
            "schema-version": "0.5",
            "suggested-resources": {
                "cpu-cores": 1,
                "ram": 1,
                "walltime-estimate": 60
            },
            "tags": {
                "purpose": "testing",
                "foo": "bar",
                "status": "example"
            },
            "tool-version": "v0.1.0"
        }

        self.count = 0
        if parser is None:
            pass
        else:
            self.parser = parser
            self.descriptor["inputs"] = []
            self.descriptor["tags"] = kwargs.get("tags") or {}
            del self.descriptor["groups"]
            del self.descriptor["output-files"]
            del self.descriptor["container-image"]
            del self.descriptor["error-codes"]
            if type(parser) is not argparse.ArgumentParser:
                raise CreatorError("Invalid argument parser")

            self.parseParser(**kwargs)

    def save(self, filename):
        import json
        with open(filename, "w") as f:
            f.write(json.dumps(self.descriptor, indent=4, sort_keys=True))

    def parseParser(self, **kwargs):
        self.descriptor["command-line"] = kwargs.get("execname")
        for act in self.parser._actions:
            tmp = self.parseAction(act, **kwargs)
            if bool(tmp):
                self.descriptor["inputs"] += [tmp]

    def parseAction(self, action, **kwargs):
        # Case 1: input is a help flag
        # Desired outcome: we skip it
        if type(action) is argparse._HelpAction:
            if kwargs.get("verbose"):
                print("_HelpAction: Skipping")
            # If this action belongs to a subparser, return a flag alongside
            # the empty object, indicating it is not required
            if kwargs.get("subaction"):
                return {}, False
            return {}

        # Case 2: input is a subparser
        # Desired outcome: we add the subparser and options, and an input for
        # each of the subparser options
        elif (type(action) is argparse._SubParsersAction and
              not kwargs.get("addParser")):
            if kwargs.get("verbose"):
                print("_SubParsersAction: Interpretting & Adding")

            # First, add the subparser itself as an input.
            subparser = self.parseAction(action, addParser=True)
            subparser["value-requires"] = {}
            inpts = {}
            # For every option specified by the subparser...
            for act in subparser["value-choices"]:
                inpts[act] = []
                subparser["value-requires"][act] = []
                # ... And for each choice specified by each subparser...
                for subact in action.choices[act]._actions:

                    # Process the action, and record its "required" status
                    tmpinput, reqd = self.parseAction(subact, subaction=True,
                                                      **kwargs)

                    # If it's not empty, add it to an inputs dictionaryi, and
                    # add the input to the descriptor.
                    if tmpinput != {}:
                        inpts[act] += [tmpinput["id"]]
                        # If the input was required by the subparser, record it
                        if reqd:
                            subparser["value-requires"][act] += [tmpinput["id"]]
                        self.descriptor["inputs"] += [tmpinput]

            # Once all subparsers are processed, idenfity which inputs need to
            # be disabled by which subparsers.
            inpt_ids = set([inp
                            for iact in inpts
                            for inp in inpts[iact]])
            subparser["value-disables"] = {}
            for act in subparser["value-choices"]:
                # Add all IDs created by the subparser that do not also belong
                # to the current selection to the disabled list.
                subparser["value-disables"][act] = [ckey
                                                    for ckey in inpt_ids
                                                    if ckey not in inpts[act]]
            return subparser

        # Case 3: input is a regular input
        # Desired outcome: we add it, unless it's already been added
        else:
            if kwargs.get("verbose"):
                actstring = str(type(action))
                actstring = actstring.split("'")[1].split(".")[-1]
                print("{0}: Adding".format(actstring))
            actdict = vars(action)
            if action.dest == "==SUPPRESS==":
                adest = "subparser_{0}".format(self.count)
                self.count += 1
            else:
                adest = action.dest

            # If an input already exists with this ID, don't re-add it
            if any(adest == it["id"] for it in self.descriptor["inputs"]):
                if kwargs.get("verbose"):
                    print("Duplicate: Argument won't be added multiple times"
                          " ({0})".format(adest))
                # If this action belongs to a subparser return a flag alongside
                # the empty object, indicating it is not required
                if kwargs.get("subaction"):
                    return {}, False
                return {}

            # If no argument exists yet by this name, process and add it.
            # First, by setting some reasonable defaults or obvious values,
            # and then by updating others.
            newinput = {
                "id": adest,
                "name": adest,
                "description": action.help,
                "optional": kwargs.get("subaction") or not action.required,
                "type": "String",
                "value-key": "{0}".format(adest.upper())
            }

            if action.type:
                if action.type in [int, float]:
                    newinput["type"] = "Number"
                elif action.type == list:
                    newinput["list"] = True

            if action.default:
                newinput["default-value"] = action.default

            if action.choices:
                try:
                    # Subparsers have choices in the form of OrderedDicts...
                    newinput["value-choices"] = list(action.choices.keys())
                except AttributeError as e:
                    # ... but "choice" inputs have them in the form a list.
                    newinput["value-choices"] = action.choices

            if len(action.option_strings):
                newinput["command-line-flag"] = action.option_strings[0]

            if type(action) is argparse._StoreTrueAction:
                newinput["type"] = "Flag"

            self.descriptor["command-line"] += " {0}".format(adest.upper())
            # If this action belongs to a subparser, return a flag along
            # with the object, indicating its required/not required status.
            if kwargs.get("subaction"):
                return newinput, action.required
            return newinput
