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
        self.unique_ids = []

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

    def addInputsRecursive(self, node, requires=[]):
        names = list(node.keys())
        if len(names) == 1:
            self._addInput(
                node[names[0]],
                requires,
                isList=node[names[0]]["isList"] if 'isList' in
                node[names[0]] else False)
            self.addInputsRecursive(
                node[names[0]]['children'], requires)
        elif len(names) > 1:
            for name in names:
                self._addInput(
                    node[name],
                    requires + self._getLineageChildren(node[name], []),
                    isList=node[name]["isList"] if 'isList' in
                    node[name] else False)
                # Add node with siblings to required-inputs list
                self.addInputsRecursive(
                    node[name]['children'], [node[name]['name']])
            self._addMutexGroup(names)

    def _addMutexGroup(self, arg_names):
        pretty_name = "_".join([self._getParamName(name) for name in arg_names])
        new_group = {
            "id": pretty_name,
            "name": "Mutex group with members: {0}".format(", ".join(
                [self._getStrippedName(name) for name in arg_names])),
            "members": [self._getParamName(name) for name in arg_names],
            "mutually-exclusive": True
        }
        self.descriptor['groups'].append(new_group)

    def _addInput(self, arg, requires, isList=False):
        joint_args = {**self.positional_arguments,
                      **self.optional_arguments,
                      **self.commands}

        param_key = arg["id"]
        param_name = arg["name"]

        new_inp = {
            "id": param_name.replace("-", "_"),
            "name": param_name,
            "description": joint_args[param_key].get('description') if
            param_key in joint_args else "",
            "optional": True,
            "value-key": "[{0}]".format(param_name).upper()
        }
        if requires != []:
            new_inp["requires-inputs"] = requires
        # Only add list param when isList
        if isList:
            new_inp['list'] = True
        if 'type' in joint_args[param_key]:
            new_inp['type'] = joint_args[param_key]['type']
        elif param_key in self.optional_arguments:
            new_inp['type'] = "Flag"
            new_inp['command-line-flag'] = joint_args[param_key]['long']
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
                        list_arg, ancestors=ancestors, isList=True)
                    ancestors.append(list_name)
                elif arg_type == "Optional" and fchild_type == "Option":
                    for option in arg.children:
                        self._addArgumentToDependencies(
                            option, ancestors=ancestors)
                elif arg_type == "Optional" and fchild_type == "Either":
                    grp_arg = self._addMutexInput(arg)
                    self._addArgumentToDependencies(
                        grp_arg, ancestors=ancestors, optional=True)
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
                self._addArgumentToDependencies(
                    arg, ancestors=ancestors, optional=True)
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
        return grp_arg

    def _addArgumentToDependencies(self, node, ancestors=None,
                                   isList=False, optional=False):
        parent_dependency = self._getDependencyParentNode(ancestors)
        argAdded = None
        print(node.name, end=": ")
        print(optional)
        if ancestors == [] and node.name not in self.dependencies:
            argAdded = self.dependencies[node.name] = {
                "id": node.name,
                "name": self._getUniqueId(self._getParamName(node.name)),
                "optional": optional,
                "parent": None,
                "children": {}}
        elif ancestors != [] and parent_dependency is not None:
            argAdded = parent_dependency['children'][node.name] = {
                "id": node.name,
                "name": self._getUniqueId(self._getParamName(node.name)),
                "optional": optional,
                "parent": parent_dependency,
                "children": {}}

        if argAdded is not None and isList:
            argAdded["isList"] = True

    def _getLineageChildren(self, node, descendants):
        child_keys = list(node['children'].keys())
        if len(child_keys) == 1 and\
           not node['children'][child_keys[0]]['optional']:
            descendants.append(node['children'][child_keys[0]]['name'])
            self._getLineageChildren(
                node['children'][child_keys[0]], descendants)
        return descendants

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

    def _getUniqueId(self, name):
        id_count = 1
        while name + (str(id_count) if id_count > 1 else "") in self.unique_ids:
            id_count += 1
        new_unique_id = name + (str(id_count) if id_count > 1 else "")
        self.unique_ids.append(new_unique_id)
        return new_unique_id

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
            for char in chars:
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
helper.addInputsRecursive(helper.dependencies)

with open(sample_dir + "sample2_descriptor_output.json", "w+") as output:
    output.write(json.dumps(helper.descriptor, indent=4))
