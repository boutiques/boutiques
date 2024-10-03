#!/usr/bin/env python

import textwrap
from argparse import ArgumentParser, RawTextHelpFormatter

from tabulate import tabulate


class PrettyPrinter:
    # Prints descriptor help text in a pretty format by first creating an
    # argument parser, and then using their help text formatting.
    def __init__(self, descriptor):
        self.sep = "".join(["="] * 80)
        self.desc = descriptor
        self.epilog = ""
        self.createHelpText()

    def createHelpText(self):
        self.createLUT()
        self.descMetadata()

        # Add container information - if applicable
        if self.desc.get("container-image"):
            self.descContainer()

        # Add system requirements - if applicable
        if self.desc.get("suggested-resources"):
            self.descResources()

        # Add error codes - if applicable
        if self.desc.get("error-codes"):
            self.descErrors()

        # Add group information - if applicable
        if self.desc.get("groups"):
            self.descGroups()

        # Add output information - if applicable
        if self.desc.get("output-files"):
            self.descOutputs()

        self.descInputs()
        self.parser.epilog = self.epilog
        self.docstring = self.parser.format_help()
        self.docstring = "\n\n".join(self.docstring.split("\n\n")[1:])

    def createLUT(self):
        # Creates two look-up tables: from ids to value-keys, and the reverse
        if self.desc.get("output-files"):
            self.CLfields = self.desc["inputs"] + self.desc["output-files"]
        else:
            self.CLfields = self.desc["inputs"]

        tmplut = {inp["id"]: inp.get("value-key") for inp in self.CLfields}
        self.lut = {
            inp.get("value-key"): [
                t for t in tmplut.keys() if tmplut[t] == inp.get("value-key")
            ]
            for inp in self.CLfields
            if inp.get("value-key")
        }

    def descMetadata(self):
        # Gather main description and basic metadata
        name = (
            f"Tool name: {self.desc['name']} "
            f"(ver: {self.desc.get('tool-version')})"
        )
        description = f"Tool description: {self.desc['description']}"
        if self.desc.get("tags"):
            taglist = [
                (
                    f"{k}: {v}"
                    if not isinstance(v, list)
                    else f"{k}: {', '.join(v)}"
                )
                for k, v in self.desc["tags"].items()
            ]
            tags = f"Tags: {'; '.join(taglist)}"
        else:
            tags = ""

        # Grabs command-line, and wraps it right to the first element of it
        # (usually the executable) unless it's too long
        cline = self.desc["command-line"]
        cend = min(len(cline.split(" ")[0]) + 1, 35)
        cline = textwrap.wrap(
            "  " + self.desc["command-line"],
            subsequent_indent="  " + " " * cend,
        )
        cline = "\\n".join(cline)
        cline = f"Command-line:\n{cline}"

        # Initialize the tool description with the pieces we've collected so far
        self.helptext = "{0}\n\n{1}\n{2}\n{3}\n\n{4}\n\n{0}" "".format(
            self.sep, name, description, tags, cline
        )

    def descContainer(self):
        conimage = self.desc["container-image"]
        container_info = "Container Information:\n"
        container_info += "\t"
        container_info += "\n\t".join(
            [f"{k.title()}: {conimage[k]}" for k in conimage.keys()]
        )
        self._addSegment(container_info)

    def descOutputs(self):
        outputs = self.desc["output-files"]
        output_info = "Output Files:"
        config_info = "Config Files:"
        for output in outputs:
            required = "Optional" if output.get("optional") else "Required"
            temp_info = f"\n  Name: {output['name']} ({required})"
            temp_info += f"\n\tFormat: {output['path-template']}"

            # Identifies input dependencies based on filename
            depids = [
                "/".join(self.lut[inp])
                for inp in self.lut.keys()
                if inp in output["path-template"]
            ]
            if depids:
                temp_info += (
                    f"\n\tFilename depends on Input IDs: {', '.join(depids)}"
                )

            # Gets stripped extensions
            if output.get("path-template-stripped-extensions"):
                exts = ", ".join(output["path-template-stripped-extensions"])
                temp_info += (
                    f"\n\tStripped extensions (before substitution): {exts}"
                )

            # If a config file, add the template
            if output.get("file-template"):
                temp_info += "\n\tTemplate:\n\t {}" "".format(
                    "\n\t ".join(output["file-template"])
                )
                config_info += temp_info
            else:
                output_info += temp_info

        self.epilog = (
            f"\n\n{self.sep}\n\n{config_info}"
            if config_info != "Config Files:"
            else ""
        )
        self.epilog += f"\n\n{self.sep}\n\n{output_info}"

    def descGroups(self):
        groups = self.desc["groups"]
        gtypes = ["Mutually Exclusive", "All or None", "One is Required"]
        group_info = "Input Groups:"
        for group in groups:
            gtype = []
            gtype += [0] if bool(group.get("mutually-exclusive")) else []
            gtype += [1] if bool(group.get("all-or-none")) else []
            gtype += [2] if bool(group.get("one-is-required")) else []
            group_info += f"\n\tName: {group['name'].title()}"
            group_info += (
                f"\n\tType: {', '.join([gtypes[ind] for ind in gtype])}\n"
            )
            group_info += f"\tGroup Member IDs: {', '.join(group['members'])}"
            group_info += "\n"
        self._addSegment(group_info)

    def descResources(self):
        res = self.desc["suggested-resources"]
        res_info = "Suggested Resources:"
        for rkey in res.keys():
            kx = rkey.replace("-", " ").title()
            res_info += f"\n\t{kx}: {res[rkey]}"
            if rkey == "ram":
                res_info += " GB"
            elif rkey == "walltime-estimate":
                res_info += " s"
        res_info += "\n"
        self._addSegment(res_info)

    def descErrors(self):
        ecod = self.desc["error-codes"]
        ecod_info = "Error Codes:"
        for ecod_obj in ecod:
            ecod_info += "\n\tReturn Code: {}\n\tDescription: {}\n" "".format(
                ecod_obj["code"], ecod_obj["description"]
            )
        ecod_info += "\n"
        self._addSegment(ecod_info)

    def descInputs(self):
        self.parser = ArgumentParser(
            description=self.helptext,
            formatter_class=RawTextHelpFormatter,
            add_help=False,
        )
        inputs = self.CLfields
        required = self.parser.add_argument_group("required arguments")

        # For every command-line key (i.e. input)...
        for clkey in self.lut.keys():
            # Re-initialize an empty argument
            inp_args = []
            inp_kwargs = {}
            opt_inp_descr = ""
            req_inp_descr = ""
            opt_inp_desc_header = ""
            opt_inp_desc_footer = ""
            req_inp_desc_header = ""
            req_inp_desc_footer = ""

            # Get all inputs with the command-line key
            inps = [inps for inps in inputs if inps.get("value-key") == clkey]

            if not len(inps):
                continue

            # Determine if input is optional or required
            tinp = inps[0]
            cflag = tinp.get("command-line-flag")
            if cflag:
                # argparse crashes when dest is supplied and
                # argument doesn't start with '--'
                if not cflag.startswith("-"):
                    cflag = "--" + cflag
                inp_args += [cflag]
                inp_kwargs["dest"] = clkey
            else:
                inp_args += [clkey]

            # If multiple inputs of the same optionality
            # share a command-line key
            multi_opt = sum(bool(inp.get("optional")) for inp in inps) > 1
            multi_req = sum(not bool(inp.get("optional")) for inp in inps) > 1

            if multi_opt:
                opt_inp_descr += "Multiple Options...\n"
                opt_inp_desc_header = "Option {0}:\n"
                opt_inp_desc_footer = "\n"
            if multi_req:
                req_inp_descr += "Multiple Options...\n"
                req_inp_desc_header = "Option {0}:\n"
                req_inp_desc_footer = "\n"

            # For every input with the clkey (usually just 1)...
            for i_inp, inp in enumerate(inps):
                if bool(inp.get("optional")):
                    opt_inp_descr += opt_inp_desc_header.format(i_inp + 1)
                else:
                    req_inp_descr += req_inp_desc_header.format(i_inp + 1)

                # Grab basic input fields first
                tmp_inp_descr = (
                    "ID: {}\nValue Key: {}\nType: {}\n"
                    "List: {}\nOptional: {}\n"
                    "".format(
                        inp.get("id"),
                        inp.get("value-key"),
                        inp.get("type"),
                        bool(inp.get("list")),
                        bool(inp.get("optional")),
                    )
                )

                # If it's a list, get min and max length and present it sensibly
                if inp.get("list"):
                    milen = inp.get("min-list-entries")
                    malen = inp.get("max-list-entries")
                    if milen and malen:
                        listlen = f"{milen} - {malen}"
                    elif milen:
                        listlen = f">= {milen}"
                    elif malen:
                        listlen = f"<= {malen}"
                    else:
                        listlen = "N/A"
                    tmp_inp_descr += f"List Length: {listlen}\n"

                # If it's a number, get min and max values and exclusivity and
                # present it as a standard number range. Also identify if an Int
                if inp.get("type") == "Number":
                    tmp_inp_descr += f"Integer: {bool(inp.get('integer'))}\n"
                    minum = inp.get("minimum") or "N/A"
                    manum = inp.get("maximum") or "N/A"
                    emi = "(" if inp.get("exclusive-minimum") else "["
                    ema = ")" if inp.get("exclusive-maximum") else "]"
                    tmp_inp_descr += f"Range: {emi}{minum}, {manum}{ema}\n"

                # If there are options, add this to the parser and the default
                # to the description
                if inp.get("value-choices"):
                    inp_kwargs["choices"] = inp["value-choices"]
                if inp.get("default-value"):
                    inp_kwargs["default"] = inp["default-value"]
                    tmp_inp_descr += f"Default Value: {inp['default-value']}\n"

                # Show exclusivity with other inputs
                if inp.get("disables-inputs"):
                    tmp_inp_descr += (
                        f"Disables: {', '.join(inp['disables-inputs'])}\n"
                    )
                if inp.get("requires-inputs"):
                    tmp_inp_descr += (
                        f"Requires: {', '.join(inp['requires-inputs'])}\n"
                    )

                # Show exclusivity of values with other inputs
                if inp.get("value-disables") and inp.get("value-requires"):
                    tmp_table_headers = ["Value", "Disables", "Requires"]
                    tmp_table = []
                    vdtab = inp["value-disables"]
                    vrtab = inp["value-requires"]
                    for tkey in vdtab:
                        tmp_table += [
                            [
                                tkey,
                                ", ".join(vdtab[tkey]),
                                ", ".join(vrtab[tkey]),
                            ]
                        ]
                    tmp_table = tabulate(tmp_table, headers=tmp_table_headers)
                    tmp_inp_descr += f"Value Dependency: \n {tmp_table}\n"

                # Finally, add the actual description
                if inp.get("description"):
                    descr_text = f"Description: {inp['description']}"
                else:
                    descr_text = ""

                if bool(inp.get("optional")):
                    opt_inp_descr += (
                        tmp_inp_descr
                        + textwrap.fill(descr_text, subsequent_indent=" ")
                        + opt_inp_desc_footer
                    )
                else:
                    req_inp_descr += (
                        tmp_inp_descr
                        + textwrap.fill(descr_text, subsequent_indent=" ")
                        + req_inp_desc_footer
                    )

            # Add args for required inputs
            if req_inp_descr != "":
                inp_kwargs["help"] = textwrap.dedent(req_inp_descr)
                required.add_argument(*inp_args, **inp_kwargs)

            # Add args for optional inputs
            if opt_inp_descr != "":
                inp_kwargs["help"] = textwrap.dedent(opt_inp_descr)
                parsed_flags = list(self.parser._option_string_actions.keys())
                for i in range(0, len(parsed_flags)):
                    if "_DUP" in parsed_flags[i]:
                        parsed_flags[i] = parsed_flags[i][0:-5]
                if inp_args[0] in parsed_flags:
                    inp_args[0] = (
                        f"{inp_args[0]}_DUP{parsed_flags.count(inp_args[0])}"
                    )
                self.parser.add_argument(*inp_args, **inp_kwargs)

    def _addSegment(self, segment):
        self.helptext += f"\n\n{segment}\n\n{self.sep}"
