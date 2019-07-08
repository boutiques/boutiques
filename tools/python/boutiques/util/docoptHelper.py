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
            self.descriptor = {
                "inputs": []
            }

        self.docopt_str = docopt_str
        self.dependencies = {}
        self.all_desc_and_type = {}
        self.unique_ids = {}
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

    def loadDocoptDescription(self):
        self.descriptor["description"] = self.docopt_str\
            .replace("".join(dcpt.parse_section(
                'usage:', self.docopt_str)), "")\
            .replace("".join(dcpt.parse_section(
                'arguments:', self.docopt_str)), "")\
            .replace("".join(dcpt.parse_section(
                'options:', self.docopt_str)), "")\
            .replace("\n\n", "\n").strip()

    def loadDescriptionAndType(self):
        # using docopt code to extract description and type from args
        for line in (dcpt.parse_section('arguments:', self.docopt_str) +
                     dcpt.parse_section('options:', self.docopt_str)):
            _, _, s = line.partition(':')  # get rid of "options:"
            split = re.split('\n[ \t]*(-\S+?)', '\n' + s)[1:] if\
                line in dcpt.parse_section('options:', self.docopt_str) else\
                re.split('\n[ \t]*(<\S+?)', '\n' + s)[1:]
            split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]
            # parse each line of Arguments and Options
            for arg_str in [s for s in split if (s.startswith('-') or
                            s.startswith('<'))]:
                arg = dcpt.Option.parse(arg_str) if arg_str.startswith('-')\
                    else dcpt.Argument.parse(arg_str)
                arg_segs = arg_str.partition('  ')
                self.all_desc_and_type[arg.name] = {
                    "desc": arg_segs[-1].replace('\n', ' ')
                                        .replace("  ", '').strip()}
                if hasattr(arg, "value") and arg.value is not None and\
                   arg.value is not False:
                    self.all_desc_and_type[arg.name]['default'] = arg.value
                if type(arg) is dcpt.Option and arg.argcount > 0:
                    for typ in [seg for seg in arg_segs[0]
                                .replace(',', ' ')
                                .replace('=', ' ')
                                .split() if seg[0] != "-"]:
                        self.all_desc_and_type[arg.name]["type"] = typ

    def generateInputsAndCommandLine(self, node):
        child_node_type = type(node.children[0]).__name__
        if hasattr(node, 'children') and (child_node_type == "Either" or
                                          child_node_type == "Required"):
            for child in node.children:
                self.generateInputsAndCommandLine(child)
        # Traversing reached usage level
        else:
            self.descriptor['command-line'] = dcpt.parse_section(
                'usage:', self.docopt_str)[0].split("\n")[1:][0].split()[0]
            self._loadInputsFromUsage(node)

    def addInputsRecursive(self, node, requires=[]):
        args_id = list(node.keys())
        if len(args_id) == 1:
            self._addInput(
                node[args_id[0]],
                requires,
                isList=node[args_id[0]]["isList"] if 'isList' in
                node[args_id[0]] else False)
            self.addInputsRecursive(
                node[args_id[0]]['children'], requires)
        elif len(args_id) > 1:
            mutex_names = []
            for name in args_id:
                self._addInput(
                    node[name],
                    requires + self._getLineageChildren(node[name], []),
                    isList=node[name]["isList"] if 'isList' in
                    node[name] else False)
                # Add node with siblings to required-inputs list
                self.addInputsRecursive(
                    node[name]['children'], [node[name]['name']])
                if not node[name]['optional']:
                    mutex_names.append(node[name]['name'])
            if len(mutex_names) > 1:
                self._addMutexGroup(mutex_names)

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
                            option, ancestors=ancestors, optional=True)
                elif arg_type == "OneOrMore":
                    list_name = "<list_of_{0}>".format(
                        self._getParamName(arg.children[0].name))
                    list_arg = dcpt.Argument(list_name)
                    list_arg.parse(list_name)
                    self.all_desc_and_type[list_name] = {
                        'desc': "List of {0}".format(
                            self._getParamName(arg.children[0].name))}
                    self._addArgumentToDependencies(
                        list_arg, ancestors=ancestors, isList=True)
                    ancestors.append(list_name)
                elif arg_type == "Optional" and fchild_type == "Option":
                    for option in arg.children:
                        self._addArgumentToDependencies(
                            option, ancestors=ancestors, optional=True)
                elif arg_type == "Optional" and fchild_type == "Either":
                    grp_arg = self._getMutexInput(arg)
                    self._addArgumentToDependencies(
                        grp_arg, ancestors=ancestors,
                        optional=True)
                    ancestors.append(grp_arg.name)
                elif arg_type == "Required" and fchild_type == "Either":
                    grp_arg = self._getMutexInput(arg)
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
        param_key = arg["id"]
        param_name = arg["name"]
        new_inp = {
            "id": param_name.replace("-", "_"),
            "name": param_name.replace("_", " ").replace("-", " "),
            "description": arg['desc'],
            "optional": True,
            "value-key": "[{0}]".format(param_name).upper()
        }
        self.descriptor["command-line"] += " {0}".format(new_inp['value-key'])

        if requires != []:
            new_inp["requires-inputs"] = requires
        # Only add list param when isList
        if isList:
            new_inp['list'] = True
        if "default" in arg:
            new_inp['default'] = arg['default']
        if "flag" in arg:
            if "type" in arg:
                new_inp['type'] = arg['type']
            else:
                new_inp['type'] = "Flag"
            new_inp["command-line-flag"] = arg["flag"]
        else:
            new_inp['type'] = "String"
        self.descriptor['inputs'].append(new_inp)

    def _getMutexInput(self, arg):
        pretty_names = []
        arg = [arg.name for arg in arg.children[0].children]
        gdesc = "Group key for mutex choices: {0}".format(
            " and ".join(arg))
        for name in arg:
            pretty_names.append(self._getStrippedName(name))
            if name in self.all_desc_and_type:
                gdesc = gdesc.replace(name, "{0} ({1})".format(
                    name, self.all_desc_and_type[name]['desc']
                ))
        gname = "<{0}>".format("_".join(pretty_names))
        grp_arg = dcpt.Argument(gname)
        grp_arg.parse(gname)
        self.all_desc_and_type[gname] = {'desc': gdesc}
        return grp_arg

    def _addArgumentToDependencies(self, node, ancestors=None,
                                   isList=False, optional=False):
        p_node = self._getDependencyParentNode(ancestors)
        argAdded = {
            "id": node.name,
            "name": self._getUniqueId(self._getParamName(node.name)),
            "optional": optional,
            "parent": None,
            "children": {}}
        if ancestors == [] and node.name not in self.dependencies:
            self.dependencies[node.name] = argAdded
        elif ancestors != [] and p_node is not None:
            argAdded["parent"] = p_node
            p_node['children'][node.name] = argAdded

        if argAdded is not None and isList:
            argAdded["isList"] = True

        argAdded["desc"] = self.all_desc_and_type[node.name]['desc']\
            if node.name in self.all_desc_and_type\
            else None

        if node.name in self.all_desc_and_type:
            if 'type' in self.all_desc_and_type[node.name]:
                argAdded["type"] = self.all_desc_and_type[node.name]['type']

            if 'default' in self.all_desc_and_type[node.name]:
                argAdded['default'] =\
                    self.all_desc_and_type[node.name]['default']

        if hasattr(node, 'long') and node.long is not None:
            # ensure flag has long hand flag
            argAdded["flag"] = node.long
            if p_node is not None and 'flag' in p_node and\
               argAdded["flag"] == p_node["flag"]:
                # if parent and child are same option (therefore has short-hand)
                # create new input with short-hand flag
                self.dependencies[
                    p_node['children'][node.name]['name']] = {
                        'id': p_node['children'][node.name]['id'],
                        'name': p_node['children'][node.name]['name'],
                        'desc': p_node['children'][node.name]['desc'],
                        'flag': node.short,
                        'optional': p_node['children'][node.name]['optional'],
                        'parent': None,
                        'children': p_node['children'][node.name]['children']}
                del p_node['children'][node.name]

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
        self.unique_ids[new_unique_id] = {'id': new_unique_id, 'original': name}
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

sample_dir = op.join(op.split(bfile)[0], 'schema/examples/'
                     'docopt_to_argparse/')
with open(sample_dir + "sample2_docopt.txt", "r") as myfile:
    sample_docopt = myfile.read()

helper = docoptHelper(sample_docopt, base_descriptor=(
    sample_dir + "defaults_docopt_descriptor.json"))
helper.loadDocoptDescription()
helper.loadDescriptionAndType()
helper.generateInputsAndCommandLine(helper.pattern)
helper.addInputsRecursive(helper.dependencies)

with open(sample_dir + "sample2_descriptor_output.json", "w+") as output:
    output.write(json.dumps(helper.descriptor, indent=4))
