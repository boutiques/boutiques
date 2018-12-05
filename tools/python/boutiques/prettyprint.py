#!/usr/bin/env python

from argparse import ArgumentParser, RawTextHelpFormatter
import prettytable
import textwrap


# Prints descriptor help text in a pretty format by first creating an argument
# parser, and then using their help text formatting.
def pprint(descriptor):
    # Create parser description, including: ...
    # Main description
    sep = "".join(["="] * 80)
    name = "Tool name: {0} (ver: {1})".format(descriptor['name'],
                                              descriptor.get("tool-version"))
    description = "Tool description: {0}".format(descriptor['description'])
    if descriptor.get("tags"):
        tags = "Tags: {0}".format(", ".join(descriptor.get("tags")))
    else:
        tags = ""

    clkeys_lut1 = {inp["id"]: inp.get("value-key")
                   for inp in (descriptor["inputs"] +
                               descriptor.get("output-files"))}
    clkeys_lut2 = {inp.get("value-key"): [t
                                      for t in clkeys_lut1.keys()
                                      if clkeys_lut1[t] == inp.get('value-key')]
                   for inp in (descriptor["inputs"] +
                               descriptor.get("output-files"))
                   if inp.get("value-key")}
    cline = descriptor['command-line']
    cend = len(cline)
    for clkey in clkeys_lut2.keys():
        cend = cline.find(clkey) if 0 < cline.find(clkey) < cend else cend
    cline = textwrap.wrap("  " + descriptor['command-line'],
                          subsequent_indent='  ' + ' ' * cend)
    cline = "Command-line:\n{0}".format("\n".join(cline))
    tool_description = ("{0}\n\n{1}\n{2}\n{3}\n\n{4}\n\n{0}"
                        "".format(sep, name, description, tags, cline))

    # Container information
    conimage = descriptor.get("container-image")
    if conimage:
        container_info = "Container Information:\n"
        container_info += "\t"
        container_info += "\n\t".join(["{0}: {1}".format(k.title(), conimage[k])
                                       for k in conimage.keys()])
        tool_description += "\n\n{0}\n\n{1}".format(container_info, sep)

    # Output information
    outputs = descriptor.get("output-files")
    if outputs:
        output_info = "Output Files:"
        for output in outputs:
            required = "Optional" if output.get("optional") else "Required"
            output_info += "\n\tName: {0} ({1})".format(output["name"],
                                                        required)

            output_info += "\n\tFormat: {0}".format(output["path-template"])

            depids = ["/".join(clkeys_lut2[inp])
                      for inp in clkeys_lut2.keys()
                      if inp in output["path-template"]]
            if depids:
                output_info += ("\n\tFilename depends on Input IDs: "
                                "{0}".format(", ".join(depids)))

            if output.get("path-template-stripped-extensions"):
                exts = ", ".join(output["path-template-stripped-extensions"])
                output_info += ("\n\tStripped extensions (before substitution):"
                                " {0}".format(exts))
            else:
                exts = ""

            if output.get("file-template"):
               output_info += ("\n\tTemplate:\n\t {0}"
                               "".format("\n\t ".join(output["file-template"])))
            output_info += "\n"
        tool_description += "\n\n{0}\n{1}".format(output_info, sep)

    # Group information
    groups = descriptor.get("groups")
    gtypes = ["Mutually Exclusive", "All or None", "One is Required"]
    if groups:
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
        tool_description += "\n\n{0}\n{1}".format(group_info, sep)

    # System requirements
    res = descriptor.get("suggested-resources")
    if res:
        res_info = "Suggested Resources:"
        for rkey in res.keys():
            kx = rkey.replace('-', ' ').title()
            res_info += "\n\t{0}: {1}".format(kx, res[rkey])
            if rkey == "ram":
                res_info += " GB"
            elif rkey == "walltime-estimate":
                res_info += " s"
        res_info += "\n"
        tool_description += "\n\n{0}\n{1}".format(res_info, sep)

    # Error Codes
    ecod = descriptor.get("error-codes")
    if ecod:
        ecod_info = "Error Codes:"
        for ecod_obj in ecod:
           ecod_info += ("\n\tReturn Code: {0}\n\tDescription: {1}\n"
                         "".format(ecod_obj["code"], ecod_obj["description"]))
        ecod_info += "\n"
        tool_description += "\n\n{0}\n{1}".format(ecod_info, sep)

    # For each input, create, including:
    parser = ArgumentParser(description=tool_description,
                            formatter_class=RawTextHelpFormatter,
                            add_help=False)
    inputs = descriptor["inputs"] + descriptor.get("output-files")
    # For every command-line key...
    for clkey in clkeys_lut2.keys():
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

        if len(inps) > 1:
            inp_descr += "Multiple Options...\n"
            inp_desc_header = "Option {0}:\n"
            inp_desc_footer = "\n"
        else:
            inp_desc_header = ""
            inp_desc_footer = ""

        for i_inp, inp in enumerate(inps):
            inp_descr += inp_desc_header.format(i_inp + 1)
            tmp_inp_descr = ("ID: {0}\nValue Key: {1}\nType: {2}\n"
                             "List: {3}\nOptional: {4}\n"
                             "".format(inp.get("id"),
                                       inp.get("value-key"),
                                       inp.get("type"),
                                       bool(inp.get("list")),
                                       bool(inp.get("optional"))))
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

            if inp.get("type") == "Number":
                tmp_inp_descr += ("Integer: {0}\n"
                                  "".format(bool(inp.get("integer"))))
                minum = inp.get("minimum") or "N/A"
                manum = inp.get("maximum") or "N/A"
                emi = "(" if inp.get("exclusive-minimum") else "["
                ema = ")" if inp.get("exclusive-maximum") else "]"
                tmp_inp_descr += "Range: {0}{1}, {2}{3}\n".format(emi, minum,
                                                              manum, ema)


            if inp.get("value-choices"):
                inp_kwargs["choices"] = inp["value-choices"]
            if inp.get("default-value"):
                inp_kwargs["default"] = inp["default-value"]
                tmp_inp_descr += ("Default Value: {0}\n"
                                  "".format(inp['default-value']))

            if inp.get("disables-inputs"):
                tmp_inp_descr += ("Disables: {0}\n"
                                  "".format(", ".join(inp["disables-inputs"])))
            if inp.get("requires-inputs"):
                tmp_inp_descr += ("Requires: {0}\n"
                                  "".format(", ".join(inp["requires-inputs"])))

            if inp.get("value-disables") and inp.get("value-requires"):
                tmp_table = prettytable.PrettyTable(["Value",
                                                     "Disables",
                                                     "Requires"])
                vdtab = inp["value-disables"]
                vrtab = inp["value-requires"]
                for tkey in vdtab:
                    tmp_table.add_row([tkey,
                                       ", ".join(vdtab[tkey]),
                                       ", ".join(vrtab[tkey])])
                tmp_inp_descr += ("Value Dependency: \n {0}\n"
                                  "".format(tmp_table))

            if inp.get("description"):
                descr_text = "Description: {0}".format(inp["description"])
            else:
                descr_text = ""
            inp_descr += tmp_inp_descr + textwrap.fill(descr_text,
                                                       subsequent_indent=" ")
            inp_descr += inp_desc_footer

        # Add argument to parser
        inp_kwargs['help'] = textwrap.dedent(inp_descr)
        parser.add_argument(*inp_args, **inp_kwargs)
        # print(inp)
        pass

    helptext = parser.format_help()
    prettystring = "\n\n".join(helptext.split("\n\n")[1:])
    return prettystring
