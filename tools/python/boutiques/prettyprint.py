#!/usr/bin/env python

from argparse import ArgumentParser, RawTextHelpFormatter
from tabulate import tabulate
import textwrap


# Prints descriptor help text in a pretty format by first creating an argument
# parser, and then using their help text formatting.
def pprint(descriptor):
    # Create parser description, including: ...

    # Gather main description and basic metadata
    sep = "".join(["="] * 80)
    name = "Tool name: {0} (ver: {1})".format(descriptor['name'],
                                              descriptor.get("tool-version"))
    description = "Tool description: {0}".format(descriptor['description'])
    if descriptor.get("tags"):
        tags = "Tags: {0}".format(", ".join(descriptor.get("tags")))
    else:
        tags = ""

    # Creates two look-up tables: from ids to value-keys, and the reverse
    clkeys_lut1 = {inp["id"]: inp.get("value-key")
                   for inp in (descriptor["inputs"] +
                               descriptor.get("output-files"))}
    clkeys_lut2 = {inp.get("value-key"): [t
                                          for t in clkeys_lut1.keys()
                                          if clkeys_lut1[t] == inp.get(
                                                                 'value-key'
                                                               )]
                   for inp in (descriptor["inputs"] +
                               descriptor.get("output-files"))
                   if inp.get("value-key")}

    # Grabs command-line, and figures out where params start so it can display
    # it nicely :)
    cline = descriptor['command-line']
    cend = len(cline)
    for clkey in clkeys_lut2.keys():
        cend = cline.find(clkey) if 0 < cline.find(clkey) < cend else cend
    cline = textwrap.wrap("  " + descriptor['command-line'],
                          subsequent_indent='  ' + ' ' * cend)
    cline = "Command-line:\n{0}".format("\n".join(cline))

    # Initialize the tool description with the pieces we've collected so far
    tool_description = ("{0}\n\n{1}\n{2}\n{3}\n\n{4}\n\n{0}"
                        "".format(sep, name, description, tags, cline))

    # Add container information - if applicable
    conimage = descriptor.get("container-image")
    if conimage:
        container_info = "Container Information:\n"
        container_info += "\t"
        container_info += "\n\t".join(["{0}: {1}".format(k.title(), conimage[k])
                                       for k in conimage.keys()])
        tool_description += "\n\n{0}\n\n{1}".format(container_info, sep)

    # Add output information - if applicable
    outputs = descriptor.get("output-files")
    if outputs:
        output_info = "Output Files:"
        for output in outputs:
            required = "Optional" if output.get("optional") else "Required"
            output_info += "\n\tName: {0} ({1})".format(output["name"],
                                                        required)
            output_info += "\n\tFormat: {0}".format(output["path-template"])

            # Identifies input dependencies based on filename
            depids = ["/".join(clkeys_lut2[inp])
                      for inp in clkeys_lut2.keys()
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
        tool_description += "\n\n{0}\n{1}".format(output_info, sep)

    # Add group information - if applicable
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

    # Add system requirements - if applicable
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

    # Add error codes - if applicable
    ecod = descriptor.get("error-codes")
    if ecod:
        ecod_info = "Error Codes:"
        for ecod_obj in ecod:
            ecod_info += ("\n\tReturn Code: {0}\n\tDescription: {1}\n"
                          "".format(ecod_obj["code"], ecod_obj["description"]))
        ecod_info += "\n"
        tool_description += "\n\n{0}\n{1}".format(ecod_info, sep)

    # Now on to inputs, through creation of an actual parser...
    parser = ArgumentParser(description=tool_description,
                            formatter_class=RawTextHelpFormatter,
                            add_help=False)
    inputs = descriptor["inputs"] + descriptor.get("output-files")

    # For every command-line key (i.e. input)...
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
                tmp_inp_descr += "Range: {0}{1}, {2}{3}\n".format(emi, minum,
                                                                  manum, ema)

            # If there are options, add this to the parser and the default to
            # the description
            if inp.get("value-choices"):
                inp_kwargs["choices"] = inp["value-choices"]
            if inp.get("default-value"):
                inp_kwargs["default"] = inp["default-value"]
                tmp_inp_descr += ("Default Value: {0}\n"
                                  "".format(inp['default-value']))

            # Show exclusivity with other inputs
            if inp.get("disables-inputs"):
                tmp_inp_descr += ("Disables: {0}\n"
                                  "".format(", ".join(inp["disables-inputs"])))
            if inp.get("requires-inputs"):
                tmp_inp_descr += ("Requires: {0}\n"
                                  "".format(", ".join(inp["requires-inputs"])))

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
                                                       subsequent_indent=" ")
            inp_descr += inp_desc_footer

        # Add the newly created argument to parser
        inp_kwargs['help'] = textwrap.dedent(inp_descr)
        parser.add_argument(*inp_args, **inp_kwargs)

    # Add the broad tool description to the parser, and return the whole thing
    helptext = parser.format_help()
    prettystring = "\n\n".join(helptext.split("\n\n")[1:])
    return prettystring
