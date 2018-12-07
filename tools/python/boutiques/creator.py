#!/usr/bin/env python

import simplejson
import tempfile
import argparse
import sys
import os
import json
import os.path as op
from jsonschema import validate, ValidationError
from argparse import ArgumentParser
from boutiques import __file__ as bfile
from boutiques.logger import raise_error, print_info, print_warning
import subprocess


# An exception class specific to creating descriptors.
class CreatorError(ValidationError):
    pass


class CreateDescriptor(object):
    def __init__(self, parser=None, **kwargs):
        template = op.join(op.split(bfile)[0], "templates", "basic.json")
        with open(template) as f:
            self.descriptor = simplejson.load(f)

        if(kwargs.get('docker_image')):
            self.parse_docker(self.descriptor,
                              kwargs.get('docker_image'),
                              kwargs.get('use_singularity'))

        self.sp_count = 0
        if parser is not None:
            self.parser = parser
            self.descriptor["inputs"] = []
            self.descriptor["tags"] = kwargs.get("tags") or {}
            del self.descriptor["groups"]
            del self.descriptor["output-files"]
            del self.descriptor["container-image"]
            del self.descriptor["error-codes"]
            if type(parser) is not argparse.ArgumentParser:
                raise_error(CreatorError, "Invalid argument parser")
            self.parseParser(**kwargs)

    def save(self, filename):
        import json
        with open(filename, "w") as f:
            f.write(json.dumps(self.descriptor, indent=4, sort_keys=True))

    def createInvocation(self, arguments):
        argdict = vars(arguments)
        argdict = {k: v for k, v in argdict.items() if v is not None}
        return argdict

    def parse_docker(self, descriptor, docker_image_name, use_singularity):
        cont_image = {}

        # Basic image config
        if use_singularity:
            cont_image['type'] = 'singularity'
            cont_image['index'] = 'docker://'
            cont_image['image'] = docker_image_name
        else:
            cont_image['type'] = 'docker'
            cont_image['image'] = docker_image_name

        descriptor['container-image'] = cont_image

        # If Docker isn't installed, that's all we can do!
        if subprocess.Popen("type docker", shell=True).wait():
            return

        # If Docker is here, let's fetch metadata from the image
        # Properties found in the image metadata
        ((stdout, stderr),
         returncode) = self.executor("docker pull "+docker_image_name)
        if returncode:
            raise_error(CreatorError, "Cannot pull Docker image {0}: {1} "
                        "{2} {3}".format(docker_image_name, stdout,
                                         os.linesep, stderr))
        ((stdout, stderr),
         returncode) = self.executor("docker inspect "+docker_image_name)
        if returncode:
            raise_error(CreatorError, "Cannot inspect Docker image {0}: {1} "
                        "{2} {3}".format(docker_image_name, stdout,
                                         os.linesep, stderr))
        image_attrs = json.loads(stdout.decode("utf-8"))[0]
        if (image_attrs.get('ContainerConfig')):
            container_config = image_attrs['ContainerConfig']
            entrypoint = container_config.get('Entrypoint')
            if entrypoint:
                cont_image['entrypoint'] = True
                tokens = descriptor['command-line'].split(" ")
                # Replace the first token in the command line template,
                # presumably the executable, by the entry point
                descriptor['command-line'] = (" ".join(entrypoint +
                                              tokens[1:])
                                              )
                descriptor['name'] = entrypoint[0]
            workingDir = container_config.get('WorkingDir')
            if workingDir:
                raise_error(CreatorError, "The container image has a working "
                            "dir, this is currently not supported.")
        if image_attrs.get('Author'):
            descriptor['author'] = image_attrs.get('Author')
        if image_attrs.get('RepoTags'):
            descriptor['tool-version'] = " ".join(image_attrs.get('RepoTags'))
        if image_attrs.get('Comment'):
            descriptor['description'] = image_attrs.get('Comment')

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
                print_info("_HelpAction: Skipping")
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
                print_info("_SubParsersAction: Interpretting & Adding")

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

            # Once all subparsers are processed, identify which inputs need to
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
                print_info("{0}: Adding".format(actstring))
            actdict = vars(action)
            if action.dest == "==SUPPRESS==":
                adest = "subparser_{0}".format(self.sp_count)
                if kwargs.get("verbose"):
                    print_warning("Subparser has no destination set, "
                                  "invocation parsing may not work as "
                                  "expected. This can be fixed by adding "
                                  "\"dest='mysubparser'\" to subparser "
                                  "creation.")
                self.sp_count += 1
            else:
                adest = action.dest

            # If an input already exists with this ID, don't re-add it
            if any(adest == it["id"] for it in self.descriptor["inputs"]):
                if kwargs.get("verbose"):
                    print_info("Duplicate: Argument won't be added multiple "
                               "times ({0})".format(adest))
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
                "value-key": "[{0}]".format(adest.upper().strip("[]"))
            }

            if action.type is not None:
                if action.type in [int, float]:
                    newinput["type"] = "Number"
                if action.type == list:
                    newinput["list"] = True

            if action.nargs is not None:
                if ((isinstance(action.nargs, str) and action.nargs == "+")
                   or (isinstance(action.nargs, int) and action.nargs > 1)):
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

            self.descriptor["command-line"] += " [{0}]".format(
                                                    adest.upper().strip("[]"))
            # If this action belongs to a subparser, return a flag along
            # with the object, indicating its required/not required status.
            if kwargs.get("subaction"):
                return newinput, action.required
            return newinput

    def executor(self, command):
        try:
            process = subprocess.Popen(command, shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        except OSError as e:
            sys.stderr.write('OS Error during attempted execution!')
            raise e
        except ValueError as e:
            sys.stderr.write('Input Value Error during attempted execution!')
            raise e
        else:
            return process.communicate(), process.returncode
