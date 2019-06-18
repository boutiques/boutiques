import re
import sys
import os.path as op
import docopt as dcpt
import simplejson as json
from argparse import ArgumentParser
from boutiques import __file__ as bfile


class docoptHelper():

    def __init__(self):
        self.descriptor = {}

        self.positional_arguments = {}
        self.optional_arguments = {}

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
                self.positional_arguments[prm.name[1:-1]] = {"value": prm.value}
            elif type(prm) is dcpt.Option:
                self.optional_arguments[prm.name[2:]] =\
                    {"value": prm.value,
                     "short": prm.short,
                     "long:": prm.long,
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
        self.descriptor["command-line"] = self.dcpt_cmdl[0].split()[1]

        # Match params in command line with extracted pos_args
        for arg in self.dcpt_cmdl[0].split()[2:]:
            if arg == "[options]":
                for opt in self.optional_arguments:
                    self.descriptor["command-line"] +=\
                        " [{0}]".format(opt.upper())
            elif arg[1:-1] in self.positional_arguments:
                self.descriptor["command-line"] +=\
                    " [{0}]".format(arg[1:-1].upper())
            else:
                print("{0} not added to command line".format(arg))

    def _loadDescription(self, docopt_str):
        self.descriptions = docopt_str\
            .replace("".join(self.dcpt_cmdl), "")\
            .replace("".join(self.dcpt_args), "")\
            .replace("".join(self.dcpt_opts), "")\
            .replace("\n\n", "\n").strip()
        self.descriptor["description"] = self.descriptions

    def _loadInputs(self):
        self.descriptor["inputs"] = []

        # Add positional arguments, optionality depends on type
        for inp in {**self.positional_arguments, **self.optional_arguments}:
            newInp = {
                "id": inp,
                "name": inp.replace("_", " "),
                "description":
                {**self.positional_arguments, **self.optional_arguments}[inp]
                .get('description'),
                "optional": inp in self.optional_arguments,
                "type": "String" if inp in self.positional_arguments else None,
                "value-key": "[{0}]".format(inp.upper())
            }
            self.descriptor['inputs'].append(newInp)

        for inp in [inp for inp in self.descriptor['inputs']
                    if inp['type'] is None]:
            inp['type'] = self.optional_arguments[inp['id']].get('type') if\
                self.optional_arguments[inp['id']].get('type') is not None else\
                "Flag"

    def generateDescriptor(self, docopt_str):
        extc_dict = dcpt.docopt(docopt_str)

        self.dcpt_cmdl = dcpt.parse_section('usage:', docopt_str)
        self.dcpt_args = dcpt.parse_section('arguments:', docopt_str)
        self.dcpt_opts = dcpt.parse_section('options:', docopt_str)

        self._importDocopt(docopt_str)
        self._loadCommandLine()
        self._loadDescription(docopt_str)
        self._loadInputs()

        return self.descriptor


sample_docopt_path = op.join(op.split(bfile)[0], 'schema/examples/'
                             'docopt_to_argparse/'
                             'sample_docopt.txt')
with open(sample_docopt_path, "r") as myfile:
    sample_docopt = myfile.read()
desc = docoptHelper().generateDescriptor(sample_docopt)

print(json.dumps(desc.get("inputs"), indent=4))
