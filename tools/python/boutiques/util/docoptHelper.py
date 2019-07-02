import re
import sys
import os.path as op
import docopt as dcpt
import simplejson as json
from argparse import ArgumentParser
from boutiques import __file__ as bfile


class docoptHelper():

    def __init__(self, docopt_str, base_descriptor=None):
        if base_descriptor is not None:
            with open(base_descriptor, "r") as base_desc:
                self.descriptor = json.load(base_desc)
        else:
            self.descriptor = {}

        self.docopt_str = docopt_str
        self.positional_arguments = {}
        self.optional_arguments = {}
        self.commands = {}
        self.dependencies = {}

        self.dcpt_usgs = dcpt.parse_section(
            'usage:', docopt_str)[0].split("\n")[1:]
        self.dcpt_args = dcpt.parse_section('arguments:', docopt_str)
        self.dcpt_opts = dcpt.parse_section('options:', docopt_str)
        options = dcpt.parse_defaults(docopt_str)

        self.pattern = dcpt.parse_pattern(
            dcpt.formal_usage(dcpt.parse_section('usage:', docopt_str)[0]),
            options)

        argv = dcpt.parse_argv(dcpt.Tokens(sys.argv[1:]), list(options), False)
        pattern_options = set(self.pattern.flat(dcpt.Option))

        for options_shortcut in self.pattern.flat(dcpt.OptionsShortcut):
            doc_options = dcpt.parse_defaults(docopt_str)
            options_shortcut.children = list(set(doc_options) - pattern_options)
        matched, left, collected = self.pattern.fix().match(argv)

    def loadArguments(self):
        for prm in self.pattern.flat():
            if type(prm) is dcpt.Argument:
                self.positional_arguments[prm.name] = {
                    "default": prm.value}
            elif type(prm) is dcpt.Command:
                self.commands[prm.name] = {
                    "default": prm.value}
            elif type(prm) is dcpt.Option:
                self.optional_arguments[prm.name] = {
                    "default": prm.value,
                    "short": prm.short,
                    "long": prm.long,
                    "argcount": prm.argcount}
            else:
                raise EnvironmentError(
                    "Unrecognized argument of type {0}\n\"{1}\": {2}".format(
                        type(prm), prm.name, prm.value))

    def loadDocoptDescription(self):
        self.descriptor["description"] = self.docopt_str\
            .replace("".join(dcpt.parse_section(
                'usage:', self.docopt_str)), "")\
            .replace("".join(self.dcpt_args), "")\
            .replace("".join(self.dcpt_opts), "")\
            .replace("\n\n", "\n").strip()

    def loadDescriptionAndType(self):
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
                # Add description field to arguments dicts
                {**self.optional_arguments, **self.positional_arguments}[
                    arg.name]["description"] = ''.join(arg_segs[2:])\
                    .replace("\n", " ").replace("  ", "").strip()
                # if type is specified add type field to optional arguments
                if type(arg) is dcpt.Option and arg.argcount > 0:
                    for typ in [seg for seg in arg_segs[0]
                                .replace(',', ' ')
                                .replace('=', ' ')
                                .split() if seg[0] != "-"]:
                        self.optional_arguments[arg.name]["type"] = typ

    def generateInputs(self, node):
        child_node_type = type(node.children[0]).__name__
        if hasattr(node, 'children') and (child_node_type == "Either" or
                                          child_node_type == "Required"):
            for child in node.children:
                self.generateInputs(child)
        # Traversing reached usage level
        else:
            self._loadInputsFromUsage(node)

    def addInputsRecursive(self, node, tabs=0):
        names = [name for name in node['children']]
        if len(node['children']) == 1:
            self._addInput(names[0])
        elif len(node['children']) > 1:
            pretty_name = "_or_".join(self._getStrippedName(names))
            choices = {}
            new_inp = {
                "id": pretty_name.replace("-", "_"),
                "name": pretty_name,
                "description": "Group key for usage choices: {0}".format(
                    " and ".join(names)),
                "optional": True,
                "type": "String",
                "value-key": "[{0}]".format(pretty_name).upper(),
                "value-choices": choices
            }
            self.descriptor['inputs'].append(new_inp)

        for child in node['children']:
            print(tabs * "  " + child)
            self.addInputsRecursive(node['children'][child], tabs+1)

    def _addInput(self, arg, isList=False):
        joint_args = {**self.positional_arguments,
                      **self.optional_arguments,
                      **self.commands}
        arg = arg.name if hasattr(arg, "name") else arg
        pretty_name = self._getStrippedName(arg)

        if not any(x['name'] == pretty_name for x in self.descriptor['inputs']):
            new_inp = {
                "id": pretty_name.replace("-", "_"),
                "name": pretty_name,
                "description": joint_args[arg].get('description'),
                "optional": True,
                "value-key": "[{0}]".format(pretty_name).upper()
            }
            # Only add list param when isList
            if isList:
                new_inp['list'] = True
            if 'type' in joint_args[arg]:
                new_inp['type'] = joint_args[arg]['type']
            elif arg in self.optional_arguments:
                new_inp['type'] = "Flag"
                new_inp['command-line-flag'] = joint_args[arg]['long']
            else:
                new_inp['type'] = "String"
            self.descriptor['inputs'].append(new_inp)

    def _loadInputsFromUsage(self, usage):
        ancestors = []
        for cmd_idx, arg in enumerate(usage.children):
            arg_type = type(arg).__name__
            if hasattr(arg, "children"):
                fchild_type = type(arg.children[0]).__name__
                # Has sub-arguments, maybe recurse into _loadRtrctnsFrmUsg
                # but have to deal with children in subtype
                if arg_type == "Optional" and fchild_type == "OptionsShortcut":
                    for option in arg.children[0].children:
                        self._addArgumentToDependencies(
                            option, ancestors=ancestors)
                elif arg_type == "OneOrMore":
                    list_name = "<list_of_{0}>".format(
                        self._getParamName(arg.children[0].name))
                    list_arg = dcpt.Argument(list_name)
                    list_arg.parse(list_name)
                    self.positional_arguments[list_name] = {
                        "default": None,
                        "description": "List of {0}".format(
                            self._getParamName(arg.children[0].name))}
                    self._addArgumentToDependencies(
                        list_arg, ancestors=ancestors)
                    ancestors.append(list_name)
                elif arg_type == "Optional" and fchild_type == "Option":
                    for option in arg.children:
                        self._addArgumentToDependencies(
                            option, ancestors=ancestors)
                elif arg_type == "Optional" and fchild_type == "Either":
                    grp_arg = self._addMutexInput(arg)
                    self._addArgumentToDependencies(
                        grp_arg, ancestors=ancestors)
                    ancestors.append(grp_arg.name)
                elif arg_type == "Required" and fchild_type == "Either":
                    grp_arg = self._addMutexInput(arg)
                    self._addArgumentToDependencies(
                        grp_arg, ancestors=ancestors)
                    ancestors.append(grp_arg.name)
            elif arg_type == "Command":
                self._addArgumentToDependencies(arg, ancestors=ancestors)
                ancestors.append(arg.name)
            elif arg_type == "Argument":
                self._addArgumentToDependencies(arg, ancestors=ancestors)
                ancestors.append(arg.name)
            elif arg_type == "Option":
                self._addArgumentToDependencies(arg, ancestors=ancestors)
                ancestors.append(arg.name)
            else:
                print("NON IMPLEMENTED arg_type: " + arg_type)

    def _addMutexInput(self, arg):
        pretty_names = []
        arg = [arg.name for arg in arg.children[0].children]
        for name in arg:
            pretty_names.append(self._getStrippedName(name))

        gname = "<{0}>".format("_".join(pretty_names))
        gdesc = "Group key for mutex choices: {0}".format(
            " and ".join(arg))
        self.positional_arguments[gname] = {
            "default": None,
            "description": gdesc}
        grp_arg = dcpt.Argument(gname)
        grp_arg.parse(gname)
        self._addInput(grp_arg)
        return grp_arg

    def _addArgumentToDependencies(self, node, ancestors=None):
        parent_dependency = self._getDependencyParentNode(ancestors)
        if ancestors == [] and node.name not in self.dependencies:
            self.dependencies[node.name] = {"children": {}}
        elif ancestors != [] and parent_dependency is not None:
            parent_dependency['children'][node.name] = {
                "parent": parent_dependency,
                "children": {}}

    def _getDependencyParentNode(self, ancestors):
        last_node = None
        for ancestor in ancestors:
            if last_node is None:
                last_node = self.dependencies[ancestor]
            elif ancestor in last_node['children']:
                last_node = last_node['children'][ancestor]
            else:
                return None
        return last_node

    def _getStrippedName(self, name):
        # only parses --arg and <arg>
        if name[0] == "-" and name[1] == "-":
            return name[2:]
        elif name[0] == "<" and name[-1] == ">":
            return name[1:-1]
        else:
            return name

    def _getParamName(self, param):
        # returns descriptor id compliant name
        chars = ['<', '>', '[', ']', '(', ')']
        if param[0] == "-" and param[1] == "-":
            param = param[2:].replace('-', '_')
            for char in chars:
                param = param.replace(char, "")
        elif param[0] == "<" and param[-1] == ">":
            param = param[1:-1].replace('-', '_')
            for char in chars:
                param = param.replace(char, "")
        else:
            param = param.replace(char, "")
        return param

    def _generateCmdKey(self, param):
        return "[{0}]".format(self._getParamName(param).upper())

sample_dir = op.join(op.split(bfile)[0], 'schema/examples/'
                     'docopt_to_argparse/')
with open(sample_dir + "sample2_docopt.txt", "r") as myfile:
    sample_docopt = myfile.read()

helper = docoptHelper(sample_docopt, base_descriptor=(
    sample_dir + "defaults_docopt_descriptor.json"))
helper.loadDocoptDescription()
helper.loadArguments()
helper.loadDescriptionAndType()
helper.generateInputs(helper.pattern)
for root_arg in helper.dependencies:
    helper.addInputsRecursive(helper.dependencies[root_arg])

with open(sample_dir + "sample2_descriptor_output.json", "w+") as output:
    output.write(json.dumps(helper.descriptor, indent=4))
