#!/usr/bin/env python

# Copyright 2015 - 2017:
#   The Royal Institution for the Advancement of Learning McGill University,
#   Centre National de la Recherche Scientifique,
#   University of Southern California,
#   Concordia University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import simplejson
import os.path as op
from jsonschema import ValidationError


# BIDS validation module
def validate_bids(descriptor, valid=False):

    if not valid:
        msg = "Please provide a Boutiques descriptor that has been validated."
        raise ValidationError(msg)

    errors = []

    # TODO: verify not only that all fields/keys exist, their properties, too

    # Ensure the command-line conforms to the BIDS app spec
    msg_template = "   CLIError: command-line doesn't match template: {}"
    cltemp = "mkdir -p OUTPUT_DIR; (.*) BIDS_DIR OUTPUT_DIR ANALYSIS_LEVEL"\
             " PARTICIPANT_LABEL SESSION_LABEL[\\s]*(.*)"
    cmdline = descriptor["command-line"]
    if len(re.findall(cltemp, cmdline)) < 1:
        errors += [msg_template.format(cltemp)]

    # Verify IDs are present which link to the OUTPUT_DIR
    # key bot as File and String
    ftypes = set(["File", "String"])
    msg_template = "   OutError: \"{}\" types for outdir do not match \"{}\""
    outtypes = set([inp["type"]
                    for inp in descriptor["inputs"]
                    if inp["value-key"] == "OUTPUT_DIR"])
    if outtypes != ftypes:
        errors += [msg_template.format(", ".join(outtypes), ", ".join(ftypes))]

    # Verify that analysis levels is an enumerable with some
    # subset of "paricipant", "session", and "group"
    choices = ["session", "participant", "group"]
    msg_template = " LevelError: \"{}\" is not a valid analysis level"
    alevels = [inp["value-choices"]
               for inp in descriptor["inputs"]
               if inp["value-key"] == "ANALYSIS_LEVEL"][0]
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
        if descriptor["output-files"][0]["path-template"] != "OUTPUT_DIR":
            errors += [msg_template]

    errors = None if errors == [] else errors
    if errors is None:
        print("BIDS validation OK")
    else:
        raise ValidationError("Invalid BIDS app descriptor:"
                              "\n"+"\n".join(errors))
