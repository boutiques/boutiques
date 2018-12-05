#!/usr/bin/env python

from argparse import ArgumentParser, RawTextHelpFormatter
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
    tags = "Tags: {0}".format(", ".join(descriptor.get("tags")))

    clkeys_lut1 = {inp["id"]: inp["value-key"] for inp in descriptor["inputs"]}
    clkeys_lut2 = {inp["value-key"]: [t
                                      for t in clkeys_lut1.keys()
                                      if clkeys_lut1[t] == inp['value-key']]
                   for inp in descriptor["inputs"]}
    cline = descriptor['command-line']
    cend = len(cline)
    for clkey in clkeys_lut2.keys():
        cend = cline.find(clkey) if cline.find(clkey) < cend else cend
    cline = textwrap.wrap("  " + descriptor['command-line'],
                          subsequent_indent='  ' + ' ' * cend)
    cline = "Command-line:\n{0}".format("\n".join(cline))

    # Container information
    conimage = descriptor.get("container-image")
    container_info = "Container Information:\n"
    if conimage:
        container_info += "\t"
        container_info += "\n\t".join(["{0}: {1}".format(k.title(), conimage[k])
                                       for k in conimage.keys()])
    else:
        container_info += "\tNo container information provided"

    # Output information
    outputs = descriptor.get("output-files")
    output_info = "Output Files:"
    if outputs:
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
            output_info += "\n"
    else:
        output_info += "\n\tNo output information provided\n"

    # Group information
    groups = descriptor.get("groups")
    gtypes = ["Mutually Exclusive", "All or None", "One is Required"]
    group_info = "Input Groups:"
    if groups:
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
    else:
        group_info += "\n\tNo input group information provided\n"

    # System requirements
    res = descriptor.get("suggested-resources")
    res_info = "Suggested Resources:"
    if res:
        for rkey in res.keys():
            kx = rkey.replace('-', ' ').title()
            res_info += "\n\t{0}: {1}".format(kx, res[rkey])
            if rkey == "ram":
                res_info += " GB"
            elif rkey == "walltime-estimate":
                res_info += " s"
        res_info += "\n"

    # Error Codes
    ecod = descriptor.get("error-codes")
    ecod_info = "Error Codes:"
    if ecod:
        for ecod_obj in ecod:
           ecod_info += ("\n\tReturn Code: {0}\n\tDescription: {1}\n"
                         "".format(ecod_obj["code"], ecod_obj["description"]))
        ecod_info += "\n"

    tool_description = ("{0}\n\n{1}\n{2}\n{3}\n\n{4}\n\n{0}\n\n"
                        "{5}\n\n{0}\n\n{6}\n{0}\n\n{7}\n{0}\n\n"
                        "{8}\n{0}\n\n{9}\n{0}"
                        "".format(sep, name, description, tags, cline,
                                  container_info, output_info, group_info,
                                  res_info, ecod_info))

    # For each input, create, including:
    parser = ArgumentParser(description=tool_description,
                            formatter_class=RawTextHelpFormatter,
                            add_help=False)
    inputs = descriptor["inputs"]
    # For every command-line key...
    for clkey in clkeys_lut2.keys():
        # Re-initialize an empty argument
        inp_args = []
        inp_kwargs = {}
        inp_descr = ""

        # Get all inputs with the command-line key
        inps = [inps
               for inps in inputs
               if inps['value-key'] == clkey]

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
            inp_desc_header = "Option {0}:\n  "
            inp_desc_footer = "\n"
        else:
            inp_desc_header = ""
            inp_desc_footer = ""

        for i_inp, inp in enumerate(inps):
    #   - Input description
    #   - Limits (in description)
    #   - Input disables/requires (in description)
            inp_descr += inp_desc_header.format(i_inp + 1)
            tmp_inp_descr = ("ID: {0}, Type: {1}, List: {2}, Optional: {3}"
                             "".format(inp.get("id"),
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
                    listlen = "Unspecified"
                tmp_inp_descr += (" List length: {0}"
                                  ""
                                  "".format(listlen))

            if inp.get("description"):
                tmp_inp_descr += ", Description: {0}".format(inp["description"])

            inp_descr += textwrap.fill(tmp_inp_descr, subsequent_indent="  ")
            inp_descr += inp_desc_footer

        # Add argument to parser
        inp_kwargs['help'] = textwrap.dedent(inp_descr)
        parser.add_argument(*inp_args, **inp_kwargs)
        # print(inp)
        pass

    helptext = parser.format_help()
    prettystring = "\n\n".join(helptext.split("\n\n")[1:])
    return prettystring
