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
        self.pattern = None

    def _importDocopt(self, docopt_str):
        options = dcpt.parse_defaults(docopt_str)

        self.pattern = dcpt.parse_pattern(
            dcpt.formal_usage(self.dcpt_cmdl[0]), options)
        argv = dcpt.parse_argv(dcpt.Tokens(sys.argv[1:]), list(options), False)
        pattern_options = set(self.pattern.flat(dcpt.Option))

        for options_shortcut in self.pattern.flat(dcpt.OptionsShortcut):
            doc_options = dcpt.parse_defaults(docopt_str)
            options_shortcut.children = list(set(doc_options) - pattern_options)
        matched, left, collected = self.pattern.fix().match(argv)

        for prm in self.pattern.flat():
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

    def _extractHierarchy(self):
        for root in self.pattern.children:
            # Many usages
            if type(root).__name__ == "Either" and len(root.children) > 1:
                for usage in root.children:
                    # Add arguments to list of required inputs for
                    # preceeding command
                    preceeding_cmd_idx = 0
                    for cmd_idx, arg in enumerate(usage.children):
                        if type(arg).__name__ == "Command":
                            if cmd_idx > 0:
                                parent_name = self._parseParam(usage.children[
                                    preceeding_cmd_idx].name)
                                command = next((x for x in
                                                self.descriptor[
                                                    "inputs"]
                                                if x["name"] ==
                                                arg.name),
                                               None)
                                if "requires-inputs" not in command:
                                    command["requires-inputs"] = [
                                            parent_name
                                        ]
                                else:
                                    command["requires-inputs"]\
                                        .append("list_of_{0}".format(
                                            parent_name))
                            preceeding_cmd_idx = cmd_idx
                        elif type(arg).__name__ == "Argument":
                            parent_name = self._parseParam(usage.children[
                                preceeding_cmd_idx].name)
                            leading_command = next((x for x in
                                                    self.descriptor["inputs"]
                                                    if x["name"] ==
                                                    parent_name),
                                                   None)
                            if "requires-inputs" not in leading_command:
                                leading_command["requires-inputs"] = [
                                        self._parseParam(arg.name)
                                    ]
                            else:
                                leading_command["requires-inputs"]\
                                    .append(self._parseParam(arg.name))
                        elif (type(arg).__name__ == "Required" and
                              len(arg.children) == 1 and
                              type(arg.children[0]).__name__ == "Either"):
                            inps = [self._parseParam(inp.name)
                                    .replace("-", "_") for inp in
                                    arg.children[0].children]
                            # Invalid input in list, most likely due to flag
                            if "" in inps:
                                continue
                            self.descriptor['inputs'].append({
                                "id": "_".join(inps),
                                "name": "_".join(inps),
                                "description": " or ".join(inps),
                                "optional": True,
                                "type": "String",
                                "value-choices": [inp.name for inp in
                                                  arg.children[0].children],
                                "value-key": "[{0}]".format("_".join(
                                    inps).upper())
                            })
                            parent_name = self._parseParam(usage.children[
                                preceeding_cmd_idx].name)
                            leading_command = next((x for x in
                                                    self.descriptor["inputs"]
                                                    if x["name"] ==
                                                    parent_name),
                                                   None)
                            if "requires-inputs" not in leading_command:
                                leading_command["requires-inputs"] = [
                                        "_".join(inps)
                                    ]
                            else:
                                leading_command["requires-inputs"]\
                                    .append("_".join(inps))
                        elif (type(arg).__name__ == "Optional" and
                              len(arg.children) == 1 and
                              type(arg.children[0]).__name__ == "Either"):
                                inps = [self._parseParam(inp.name)
                                        .replace("-", "_") for inp in
                                        arg.children[0].children]
                                # Invalid input in list, most likely due to flag
                                if "" in inps:
                                    continue
                                self.descriptor['inputs'].append({
                                    "id": "_".join(inps),
                                    "name": "_".join(inps),
                                    "description": " or ".join(inps),
                                    "optional": True,
                                    "type": "String",
                                    "value-choices": [inp.name for inp in
                                                      arg.children[0].children],
                                    "value-key": "[{0}]".format("_".join(
                                        inps).upper())
                                })
                        elif type(arg).__name__ == "OneOrMore":
                            # Create list_item value in inputs, clone of item
                            # but list = true
                            parent_name = self._parseParam(usage.children[
                                preceeding_cmd_idx].name)
                            inp_name = self._parseParam(arg.children[0].name)
                            self.descriptor['inputs'].append({
                                "id": "list_of_{0}".format(inp_name)
                                .replace("-", "_"),
                                "name": "list_of_{0}".format(inp_name),
                                "description": "list of {0}s".format(inp_name),
                                "optional": True,
                                "type": "String",
                                "list": True,
                                "value-key": "[{0}]".format(
                                    "list_of_{0}".format(inp_name).upper())
                            })
                            parent_name = self._parseParam(usage.children[
                                preceeding_cmd_idx].name)
                            leading_command = next((x for x in
                                                    self.descriptor["inputs"]
                                                    if x["name"] ==
                                                    parent_name),
                                                   None)
                            if "requires-inputs" not in leading_command:
                                leading_command["requires-inputs"] = [
                                        "list_of_{0}".format(inp_name)
                                    ]
                            else:
                                leading_command["requires-inputs"]\
                                    .append("list_of_{0}".format(inp_name))
        # print(json.dumps(self.descriptor["inputs"], indent=2))

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

    def generateDescriptor(self, docopt_str):
        self.dcpt_cmdl = dcpt.parse_section('usage:', docopt_str)
        self.dcpt_usgs = self.dcpt_cmdl[0].split("\n")[1:]
        self.dcpt_args = dcpt.parse_section('arguments:', docopt_str)
        self.dcpt_opts = dcpt.parse_section('options:', docopt_str)

        self._importDocopt(docopt_str)
        self._loadDescription(docopt_str)
        self._loadInputs()
        self._extractHierarchy()

        return self.descriptor


sample_dir = op.join(op.split(bfile)[0], 'schema/examples/'
                     'docopt_to_argparse/')
with open(sample_dir + "sample2_docopt.txt", "r") as myfile:
    sample_docopt = myfile.read()

desc = docoptHelper(base_descriptor=(
    sample_dir + "defaults_docopt_descriptor.json"))\
    .generateDescriptor(sample_docopt)

with open(sample_dir + "sample2_descriptor_output.json", "w+") as output:
    output.write(json.dumps(desc, indent=4))
