#!/usr/bin/env python

import re
import simplejson
import os.path as op
from boutiques.validator import DescriptorValidationError
from boutiques.logger import raise_error, print_info


# BIDS validation module
def validate_bids(descriptor, valid=False):

    if not valid:
        msg = "Please provide a Boutiques descriptor that has been validated."
        raise_error(DescriptorValidationError, msg)

    errors = []

    # TODO: verify not only that all fields/keys exist, their properties, too

    # Ensure the command-line conforms to the BIDS app spec
    msg_template = "   CLIError: command-line doesn't match template: {}"
    cltemp = r"mkdir -p \[OUTPUT_DIR\]; (.*) \[BIDS_DIR\] \[OUTPUT_DIR\]"\
             r" \[ANALYSIS_LEVEL\] \[PARTICIPANT_LABEL\] \[SESSION_LABEL\]"\
             r"[\\s]*(.*)"
    cmdline = descriptor["command-line"]
    if len(re.findall(cltemp, cmdline)) < 1:
        errors += [msg_template.format(cltemp)]

    # Verify IDs are present which link to the OUTPUT_DIR
    # key bot as File and String
    ftypes = set(["File", "String"])
    msg_template = "   OutError: \"{}\" types for outdir do not match \"{}\""
    outtypes = set([inp["type"]
                    for inp in descriptor["inputs"]
                    if inp["value-key"] == "[OUTPUT_DIR]"])
    if outtypes != ftypes:
        errors += [msg_template.format(", ".join(outtypes), ", ".join(ftypes))]

    # Verify that analysis levels is an enumerable with some
    # subset of "paricipant", "session", and "group"
    choices = ["session", "participant", "group"]
    msg_template = " LevelError: \"{}\" is not a valid analysis level"
    alevels = [inp["value-choices"]
               for inp in descriptor["inputs"]
               if inp["value-key"] == "[ANALYSIS_LEVEL]"][0]
    errors += [msg_template.format(lv)
               for lv in alevels
               if lv not in choices]

    # Verify there is only a single output defined (the directory)
    msg_template = "OutputError: 0 or multiple outputs defined"
    if len(descriptor["output-files"]) != 1:
        errors += [msg_template]
    else:
        # Verify that the output shows up as an output
        msg_template = "OutputError: OUTPUT_DIR is not represented as an output"
        if descriptor["output-files"][0]["path-template"] != "[OUTPUT_DIR]":
            errors += [msg_template]

    errors = None if errors == [] else errors
    if errors is None:
        print_info("BIDS validation OK")
    else:
        raise_error(DescriptorValidationError, "Invalid BIDS app descriptor:"
                    "\n"+"\n".join(errors))
