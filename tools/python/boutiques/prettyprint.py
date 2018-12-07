#!/usr/bin/env python

from argparse import ArgumentParser, RawTextHelpFormatter
from tabulate import tabulate
import textwrap


class PrettyPrinter():
    # Prints descriptor help text in a pretty format by first creating an
    # argument parser, and then using their help text formatting.
    def __init__(self, descriptor):
        self.sep = "".join(["="] * 80)
        self.desc = descriptor
        self.createHelpText()

    def createHelpText(self):
        self.createLUT()
        self.descMetadata()

        # Add container information - if applicable
        if self.desc.get("container-image"):
            self.descContainer()

        # Add output information - if applicable
        if self.desc.get("output-files"):
            self.descOutputs()

        # Add group information - if applicable
        if self.desc.get("groups"):
            self.descGroups()

        # Add system requirements - if applicable
        if self.desc.get("suggested-resources"):
            self.descResources()

        # Add error codes - if applicable
        if self.desc.get("error-codes"):
            self.descErrors()

        self.descInputs()

        self.docstring = self.parser.format_help()
        self.docstring = "\n\n".join(self.docstring.split("\n\n")[1:])

    def createLUT(self):
        # Creates two look-up tables: from ids to value-keys, and the reverse
        if self.desc.get("output-files"):
            self.CLfields = self.desc["inputs"] + self.desc["output-files"]
        else:
            self.CLfields = self.desc["inputs"]

        tmplut = {inp["id"]: inp.get("value-key")
                  for inp in self.CLfields}
        self.lut = {inp.get("value-key"): [t for t in tmplut.keys()
                                           if tmplut[t] == inp.get('value-key')]
                    for inp in self.CLfields if inp.get("value-key")}

    def descMetadata(self):
        # Gather main description and basic metadata
        name = "Tool name: {0} (ver: {1})".format(self.desc['name'],
                                                  self.desc.get("tool-version"))
        description = "Tool description: {0}".format(self.desc['description'])
        if self.desc.get("tags"):
            taglist = ["{0}: {1}".format(k, v) if not isinstance(v, list)
                       else "{0}: {1}".format(k, ", ".join(v))
                       for k, v in self.desc["tags"].items()]
            tags = "Tags: {0}".format("; ".join(taglist))
        else:
            tags = ""

        # Grabs command-line, and figures out where params start so it can
        # display it nicely
        cline = self.desc['command-line']
        cend = len(cline)
        for clkey in self.lut.keys():
            cend = cline.find(clkey) if 0 < cline.find(clkey) < cend else cend
        cline = textwrap.wrap("  " + self.desc['command-line'],
                              subsequent_indent='  ' + ' ' * cend)
        cline = "Command-line:\n{0}".format("\n".join(cline))

        # Initialize the tool description with the pieces we've collected so far
        self.helptext = ("{0}\n\n{1}\n{2}\n{3}\n\n{4}\n\n{0}"
                         "".format(self.sep, name, description, tags, cline))

    def descContainer(self):
        conimage = self.desc["container-image"]
        container_info = "Container Information:\n"
        container_info += "\t"
        container_info += "\n\t".join(["{0}: {1}".format(k.title(), conimage[k])
                                       for k in conimage.keys()])
        self._addSegment(container_info)

    def descOutputs(self):
        outputs = self.desc["output-files"]
        output_info = "Output Files:"
        for output in outputs:
            required = "Optional" if output.get("optional") else "Required"
            output_info += "\n\tName: {0} ({1})".format(output["name"],
                                                        required)
            output_info += "\n\tFormat: {0}".format(output["path-template"])

            # Identifies input dependencies based on filename
            depids = ["/".join(self.lut[inp])
                      for inp in self.lut.keys()
                      if inp in output["path-template"]]
            if depids:
                output_info += ("\n\tFilename depends on Input IDs: "
                                "{0}".format(", ".join(depids)))

            # Gets stripped extensions
            if output.get("path-template-stripped-extensions"):
                exts = ", ".join(output["path-template-stripped-extensions"])
                output_info += ("\n\tStripped extensions (before substitution):"
                                " {0}".format(exts))

            # If a config file, add the template
            if output.get("file-template"):
                output_info += ("\n\tTemplate:\n\t {0}"
                                "".format("\n\t ".join(
                                                    output["file-template"]
                                                  )))
            output_info += "\n"
        self._addSegment(output_info)

    def descGroups(self):
        groups = self.desc["groups"]
        gtypes = ["Mutually Exclusive", "All or None", "One is Required"]
        group_info = "Input Groups:"
        for group in groups:
            gtype = []
            gtype += [0] if bool(group.get("mutually-exclusive")) else []
            gtype += [1] if bool(group.get("all-or-none")) else []
            gtype += [2] if bool(group.get("one-is-required")) else []
            group_info += "\n\tName: {0}".format(group["name"].title())
            group_info += "\n\tType: {0}\n".format(", ".join([gtypes[ind]
                                                              for ind
                                                              in gtype]))
            group_info += ("\tGroup Member IDs: "
                           "{0}".format(", ".join(group["members"])))
            group_info += "\n"
        self._addSegment(group_info)

    def descResources(self):
        res = self.desc["suggested-resources"]
        res_info = "Suggested Resources:"
        for rkey in res.keys():
            kx = rkey.replace('-', ' ').title()
            res_info += "\n\t{0}: {1}".format(kx, res[rkey])
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
            ecod_info += ("\n\tReturn Code: {0}\n\tDescription: {1}\n"
                          "".format(ecod_obj["code"], ecod_obj["description"]))
        ecod_info += "\n"
        self._addSegment(ecod_info)

    def descInputs(self):
        self.parser = ArgumentParser(description=self.helptext,
                                     formatter_class=RawTextHelpFormatter,
                                     add_help=False)
        inputs = self.CLfields

        # For every command-line key (i.e. input)...
        for clkey in self.lut.keys():
            # Re-initialize an empty argument
            inp_args = []
            inp_kwargs = {}
            inp_descr = ""

            # Get all inputs with the command-line key
            inps = [inps
                    for inps in inputs
                    if inps.get('value-key') == clkey]

            if not len(inps):
                continue

            # Determine if input is optional or required
            tinp = inps[0]
            cflag = tinp.get("command-line-flag")
            if cflag:
                inp_args += [cflag]
                inp_kwargs['dest'] = clkey
            else:
                inp_args += [clkey]

            # If multiple inputs share a command-line key
            if len(inps) > 1:
                inp_descr += "Multiple Options...\n"
                inp_desc_header = "Option {0}:\n"
                inp_desc_footer = "\n"
            else:
                inp_desc_header = ""
                inp_desc_footer = ""

            # For every input with the clkey (usually just 1)...
            for i_inp, inp in enumerate(inps):
                inp_descr += inp_desc_header.format(i_inp + 1)

                # Grab basic input fields first
                tmp_inp_descr = ("ID: {0}\nValue Key: {1}\nType: {2}\n"
                                 "List: {3}\nOptional: {4}\n"
                                 "".format(inp.get("id"),
                                           inp.get("value-key"),
                                           inp.get("type"),
                                           bool(inp.get("list")),
                                           bool(inp.get("optional"))))

                # If it's a list, get min and max length and present it sensibly
                if inp.get("list"):
                    milen = inp.get("min-list-entries")
                    malen = inp.get("max-list-entries")
                    if milen and malen:
                        listlen = "{0} - {1}".format(milen,
                                                     malen)
                    elif milen:
                        listlen = ">= {0}".format(milen)
                    elif malen:
                        listlen = "<= {0}".format(malen)
                    else:
                        listlen = "N/A"
                    tmp_inp_descr += ("List Length: {0}"
                                      "\n"
                                      "".format(listlen))

                # If it's a number, get min and max values and exclusivity and
                # present it as a standard number range. Also identify if an Int
                if inp.get("type") == "Number":
                    tmp_inp_descr += ("Integer: {0}\n"
                                      "".format(bool(inp.get("integer"))))
                    minum = inp.get("minimum") or "N/A"
                    manum = inp.get("maximum") or "N/A"
                    emi = "(" if inp.get("exclusive-minimum") else "["
                    ema = ")" if inp.get("exclusive-maximum") else "]"
                    tmp_inp_descr += "Range: {0}{1}, {2}{3}\n".format(emi,
                                                                      minum,
                                                                      manum,
                                                                      ema)

                # If there are options, add this to the parser and the default
                # to the description
                if inp.get("value-choices"):
                    inp_kwargs["choices"] = inp["value-choices"]
                if inp.get("default-value"):
                    inp_kwargs["default"] = inp["default-value"]
                    tmp_inp_descr += ("Default Value: {0}\n"
                                      "".format(inp['default-value']))

                # Show exclusivity with other inputs
                if inp.get("disables-inputs"):
                    tmp_inp_descr += ("Disables: {0}\n"
                                      "".format(", ".join(
                                                       inp["disables-inputs"])))
                if inp.get("requires-inputs"):
                    tmp_inp_descr += ("Requires: {0}\n"
                                      "".format(", ".join(
                                                       inp["requires-inputs"])))

                # Show exclusivity of values with other inputs
                if inp.get("value-disables") and inp.get("value-requires"):
                    tmp_table_headers = ["Value", "Disables", "Requires"]
                    tmp_table = []
                    vdtab = inp["value-disables"]
                    vrtab = inp["value-requires"]
                    for tkey in vdtab:
                        tmp_table += [[tkey,
                                       ", ".join(vdtab[tkey]),
                                       ", ".join(vrtab[tkey])]]
                    tmp_table = tabulate(tmp_table, headers=tmp_table_headers)
                    tmp_inp_descr += ("Value Dependency: \n {0}\n"
                                      "".format(tmp_table))

                # Finally, add the actual description
                if inp.get("description"):
                    descr_text = "Description: {0}".format(inp["description"])
                else:
                    descr_text = ""
                inp_descr += tmp_inp_descr + textwrap.fill(descr_text,
                                                           subsequent_indent=" "
                                                           )
                inp_descr += inp_desc_footer

            # Add the newly created argument to parser
            inp_kwargs['help'] = textwrap.dedent(inp_descr)
            self.parser.add_argument(*inp_args, **inp_kwargs)

    def _addSegment(self, segment):
        self.helptext += "\n\n{0}\n\n{1}".format(segment, self.sep)
