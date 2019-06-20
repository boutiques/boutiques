import re
import sys
import os.path as op
import docopt as dcpt
import simplejson as json
from argparse import ArgumentParser
from boutiques import __file__ as bfile


class docoptHelper():
    TYPE_MAPPINGS = {
        "REGNAME": "String",
        "PATH": "File",
        "FILE": "File",
        "INT": "Number",
        "FWHM": "String",
        "STR": "String",
        "TAG": "String",
        "YAML": "String"
    }

    def __init__(self, base_descriptor=None):
        if base_descriptor is not None:
            with open(base_descriptor, "r") as base_desc:
                self.descriptor = json.load(base_desc)
        else:
            self.descriptor = {}

        self.groups = []
        self.positional_arguments = {}
        self.optional_arguments = {}
        self.commands = {}

    def _importDocopt(self, docopt_str):
        options = dcpt.parse_defaults(docopt_str)

        pattern = dcpt.parse_pattern(
            dcpt.formal_usage(self.dcpt_cmdl[0]), options)
        argv = dcpt.parse_argv(dcpt.Tokens(sys.argv[1:]), list(options), False)
        pattern_options = set(pattern.flat(dcpt.Option))

        for options_shortcut in pattern.flat(dcpt.OptionsShortcut):
            doc_options = dcpt.parse_defaults(docopt_str)
            options_shortcut.children = list(set(doc_options) - pattern_options)
        matched, left, collected = pattern.fix().match(argv)

        for prm in pattern.flat():
            if type(prm) is dcpt.Argument:
                self.positional_arguments[prm.name[1:-1]] = {
                    "default": prm.value}
            elif type(prm) is dcpt.Command:
                self.commands[prm.name] = {
                    "default": prm.value}
            elif type(prm) is dcpt.Option:
                self.optional_arguments[prm.name[2:]] = {
                    "default": prm.value,
                    "short": prm.short,
                    "long": prm.long,
                    "argcount": prm.argcount}
            else:
                raise EnvironmentError(
                    "Unrecognized argument of type {0}\n\"{1}\": {2}".format(
                        type(prm), prm.name, prm.value))

        # using docopt code to extract description and type from args
        for line in (self.dcpt_opts + self.dcpt_args):
            _, _, s = line.partition(':')  # get rid of "options:"
            split = re.split('\n[ \t]*(-\S+?)', '\n' + s)[1:] if\
                line in self.dcpt_opts else\
                re.split('\n[ \t]*(<\S+?)', '\n' + s)[1:]
            split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]
            # parse each line of Arguments and Options
            for arg_str in [s for s in split if (s.startswith('-') or
                            s.startswith('<'))]:
                arg = dcpt.Option.parse(arg_str) if arg_str.startswith('-')\
                    else dcpt.Argument.parse(arg_str)
                arg_segs = arg_str.partition('  ')
                arg_name = arg.name[2:] if type(arg) is dcpt.Option else\
                    arg.name[1:-1]
                # Add description field to arguments dicts
                {**self.optional_arguments, **self.positional_arguments}[
                    arg_name]["description"] = ''.join(arg_segs[2:])\
                    .replace("\n", " ").replace("  ", "").strip()
                # if type is specified add type field to optional arguments
                if type(arg) is dcpt.Option and arg.argcount > 0:
                    for typ in [seg for seg in arg_segs[0]
                                .replace(',', ' ')
                                .replace('=', ' ')
                                .split() if seg[0] != "-"]:
                        self.optional_arguments[arg_name]["type"] = typ

    def _loadCommandLine(self):
        command = self.dcpt_cmdl[0].split()[1]
        self.descriptor["command-line"] = command

        for arg in [arg for arg in self.dcpt_cmdl[0].split()[1:] if
                    arg != command]:
            if arg == "[options]":
                for opt in self.optional_arguments:
                    self.descriptor["command-line"] +=\
                            self._generateCmdKey(opt)
            elif arg[0] == "(" and arg[-1] == ")":
                if arg[1:-1].split("|"):
                    for option_arg in arg[1:-1].split("|"):
                        self.descriptor["command-line"] +=\
                            self._generateCmdKey(option_arg)
                else:
                    print("required arg: " + arg)
            elif arg[0] == "[" and arg[-1] == "]":
                if arg[1:-1].split("|"):
                    for option_arg in arg[1:-1].split("|"):
                        self.descriptor["command-line"] +=\
                            self._generateCmdKey(option_arg)
                else:
                    self.descriptor["command-line"] += self._generateCmdKey(arg)
            else:
                self.descriptor["command-line"] += self._generateCmdKey(arg)

    def _parseParam(self, param):
        if len(param.split("=")) > 1:
            param = param.split("=")[0]

        if param[2:] in self.optional_arguments:
            return param[2:]
        elif param[1:-1] in self.positional_arguments:
            return param[1:-1]
        elif param in self.commands or param in self.optional_arguments:
            return param
        elif param[1:-4] in self.positional_arguments:
            return param[1:-4]
        else:
            return ""

    def _generateCmdKey(self, param):
        cmdKey = " [{0}]".format(self._parseParam(param).upper())
        return "" if cmdKey == " []" or\
            cmdKey in self.descriptor["command-line"]\
            else cmdKey

    def _loadDescription(self, docopt_str):
        self.descriptions = docopt_str\
            .replace("".join(self.dcpt_cmdl), "")\
            .replace("".join(self.dcpt_args), "")\
            .replace("".join(self.dcpt_opts), "")\
            .replace("\n\n", "\n").strip()
        self.descriptor["description"] = self.descriptions

    def _loadInputs(self):
        self.descriptor["inputs"] = []

        # Add arguments, optionality depends on type
        joint_args = {**self.positional_arguments,
                      **self.optional_arguments,
                      **self.commands}
        for inp in [arg for arg in joint_args if not any(i['id'] == arg for
                    i in self.descriptor['inputs'])]:
            newInp = {
                "id": inp.replace("-", "_"),
                "name": inp,
                "description": joint_args[inp].get('description'),
                "optional": True,
                "type": "String" if inp in self.positional_arguments else None,
                "value-key": "[{0}]".format(inp.upper())
            }
            self.descriptor['inputs'].append(newInp)

        # Additional fields for optional inputs
        for inp in [inp for inp in self.descriptor['inputs']
                    if inp['name'] in self.optional_arguments]:
            if self.optional_arguments[inp['name']].get('type') is not None:
                # non flag params can have defaults
                if joint_args[inp['name']]['default'] is not None:
                    inp['default-value'] = joint_args[inp['name']]['default']
                # Get input type for optional arguments
                docopt_type = self.optional_arguments[inp['name']].get('type')
                if docopt_type in self.TYPE_MAPPINGS:
                    inp['type'] = self.TYPE_MAPPINGS[docopt_type]
                else:
                    inp['type'] = "String"
            else:
                inp['type'] = "Flag"
                inp['command-line-flag'] =\
                    self.optional_arguments[inp['name']].get('long')

    def _extractGroups(self):
        # extract together groups
        for idx, usage_line in enumerate(self.dcpt_cmdl[0].split("\n")[1:]):
            usage_group = {"id": "together_grp_{0}".format(idx),
                           "members": [],
                           "all-or-none": True,
                           "name": ""}
            for arg in [arg for arg in usage_line.split()[1:] if
                        self._parseParam(arg) != ""]:
                usage_group['members'].append(self._parseParam(arg))
            usage_group['name'] = "_".join(usage_group['members'])

            # add to groups if there's more than one member
            if len(usage_group['members']) > 1:
                self.groups.append(usage_group)

        self.descriptor['groups'] = self.groups

    def generateDescriptor(self, docopt_str):
        self.dcpt_cmdl = dcpt.parse_section('usage:', docopt_str)
        self.dcpt_args = dcpt.parse_section('arguments:', docopt_str)
        self.dcpt_opts = dcpt.parse_section('options:', docopt_str)

        self._importDocopt(docopt_str)
        self._loadCommandLine()
        self._loadDescription(docopt_str)
        self._loadInputs()
        self._extractGroups()

        return self.descriptor


sample_dir = op.join(op.split(bfile)[0], 'schema/examples/'
                     'docopt_to_argparse/')
with open(sample_dir + "sample_docopt.txt", "r") as myfile:
    sample_docopt = myfile.read()

desc = docoptHelper(base_descriptor=(
    sample_dir + "defaults_docopt_descriptor.json"))\
    .generateDescriptor(sample_docopt)

with open(sample_dir + "sample_descriptor_output.json", "w+") as output:
    output.write(json.dumps(desc, indent=4))
