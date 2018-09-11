#!/usr/bin/env python

from argparse import ArgumentParser
import textwrap

# Prints descriptor help text in a pretty format by first creating an argument
# parser, and then using their help text formatting.
def pprint(descriptor):
    # Create parser description, including: ...
    #   - Main description
    sep = "".join(["="] * 80)
    name = "Tool name: {0}".format(descriptor['name'])
    description = "Tool description: {0}".format(descriptor['description'])

    clkeys = {inp["value-key"]: inp["id"] for inp in descriptor["inputs"]}
    cline = descriptor['command-line']
    cend = len(cline)
    for clkey in clkeys.keys():
        cend = cline.find(clkey) if cline.find(clkey) < cend else cend
    cline = textwrap.wrap("  " + descriptor['command-line'],
                          subsequent_indent='  ' + ' ' * cend)
    cline = "Command-line:\n{0}".format("\n".join(cline))

    #   - Container information
    conimage = descriptor.get("container-image")
    container_info = "Container Information:\n"
    if conimage:
        container_info += "\t"
        container_info += "\n\t".join(["{0}: {1}".format(k.title(), conimage[k])
                                       for k in conimage.keys()])
    else:
        container_info += "\tNo container information provided"

    #   - Output information
    outputs = descriptor.get("output-files")
    output_info = "Output Files:"
    clkeys = {inp["value-key"]: inp["id"] for inp in descriptor["inputs"]}
    if outputs:
        for output in outputs:
            exts = ", ".join(output.get("path-template-stripped-extensions"))
            depids = [clkeys[inp]
                      for inp in clkeys.keys()
                      if inp in output["path-template"]]
            required = "Optional" if output.get("optional") else "Required"
            output_info += "\n\tName: {0} ({1})".format(output["name"],
                                                    required)
            output_info += "\n\tFormat: {0}".format(output["path-template"])
            output_info += ("\n\tFilename depends on Input IDs: "
                            "{0}".format(", ".join(depids)))
            output_info += ("\n\tStripped extensions (before substitution): "
                            "{0}".format(exts))
            output_info += "\n"
    else:
        output_info += "\n\tNo output information provided\n"

    #   - Group information
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
                                                            for ind in gtype]))
            group_info += "\tInput IDs: {0}".format(", ".join(group["members"]))
            group_info += "\n"
    else:
        group_info += "\n\tNo input group information provided"

    tool_description = """{0}\n
{1}
{2}
{3}\n
{0}\n
{4}\n
{0}\n
{5}
{0}\n
{6}\n
{0}
""".format(sep, name, description, cline, container_info,
           output_info, group_info)

    # For each input, create, including:
    #   - Input id
    #   - Input description
    #   - Input type (in description)
    #   - Limits (in description)
    #   - Input disables/requires (in description)
    #   - Required/Optional status
    #   - Command-line flag
    prettystring = tool_description
    return prettystring
