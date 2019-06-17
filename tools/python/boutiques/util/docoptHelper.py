"""
Runs a combination of fmriprep and ciftify pipelines from BIDS specification

Usage:
  fmriprep_ciftify.py <bids_dir> <output_dir> <analysis_level> [options]

Arguments:
    <bids_dir>               The directory with the input dataset formatted
                             according to the BIDS standard.
    <output_dir>             The directory where the output files should be stored.
                             If you are running ciftify on a partially run analyses see below.
    <analysis_level>         Analysis level to run (participant or group)

Options:
  --participant_label=<subjects>  String or Comma separated list of participants to process. Defaults to all.
  --task_label=<tasks>            String or Comma separated list of fmri tasks to process. Defaults to all.
  --session_label=<sessions>      String or Comma separated list of sessions to process. Defaults to all.
  --anat_only                     Only run the anatomical pipeline.
  --rerun-if-incomplete           Will delete and rerun ciftify workflows if incomplete outputs are found.
  --read-from-derivatives PATH    Indicates pre-ciftify will be read from
                                  the indicated derivatives path and freesurfer/fmriprep will not be run
  --func-preproc-dirname STR      Name derivatives folder where func derivatives are found [default: fmriprep]
  --func-preproc-desc TAG         The bids desc tag [default: preproc] assigned to the preprocessed file
  --older-fmriprep                Read from fmriprep derivatives that are version 1.1.8 or older
  --fmriprep-workdir PATH         Path to working directory for fmriprep
  --fs-license FILE               The freesurfer license file
  --n_cpus INT                    Number of cpu's available. Defaults to the value
                                  of the OMP_NUM_THREADS environment variable
  --ignore-fieldmaps              Will ignore available fieldmaps and use syn-sdc for fmriprep
  --no-SDC                        Will not do fmriprep distortion correction at all (NOT recommended)
  --fmriprep-args="args"          Additional user arguments that may be added to fmriprep stages
  --resample-to-T1w32k            Resample the Meshes to 32k Native (T1w) Space
  --surf-reg REGNAME              Registration sphere prefix [default: MSMSulc]
  --no-symlinks                   Will not create symbolic links to the zz_templates folder
  --SmoothingFWHM FWHM            Full Width at Half MAX for optional fmri cifti smoothing
  --MSM-config PATH               EXPERT OPTION. The path to the configuration file to use for
                                  MSMSulc mode. By default, the configuration file
                                  is ciftify/data/hcp_config/MSMSulcStrainFinalconf
                                  This setting is ignored when not running MSMSulc mode.
  --ciftify-conf YAML             EXPERT OPTION. Path to a yaml configuration file. Overrides
                                  the default settings in
                                  ciftify/data/ciftify_workflow_settings.yaml
  -v,--verbose                    Verbose logging
  --debug                         Debug logging in Erin's very verbose style
  -n,--dry-run                    Dry run
  -h,--help                       Print help

DETAILS

Adapted from modules of the Human Connectome
Project's minimal proprocessing pipeline. Please cite:

Glasser MF, Sotiropoulos SN, Wilson JA, Coalson TS, Fischl B, Andersson JL, Xu J,
Jbabdi S, Webster M, Polimeni JR, Van Essen DC, Jenkinson M, WU-Minn HCP Consortium.
The minimal preprocessing pipelines for the Human Connectome Project. Neuroimage. 2013 Oct 15;80:105-24.
PubMed PMID: 23668970; PubMed Central PMCID: PMC3720813.

The default outputs are condensed to include in 4 mesh "spaces" in the following directories:
  + T1w/Native: The freesurfer "native" output meshes
  + MNINonLinear/Native: The T1w/Native mesh warped to MNINonLinear
  + MNINonLinear/fsaverage_LR32k
     + the surface registered space used for fMRI and multi-modal analysis
     + This 32k mesh has approx 2mm vertex spacing
  + MNINonLinear_164k_fs_LR (in the MNINonLinear folder):
     + the surface registered space used for HCP's anatomical analysis
     + This 164k mesh has approx 0.9mm vertex spacing

In addition, the optional flag '--resample-to-T1w32k' can be used to output an
additional T1w/fsaverage_LR32k folder that occur in the HCP Consortium Projects.
These outputs can be critical for those building masks for DWI tract tracing.

By default, some to the template files needed for resampling surfaces and viewing
flatmaps will be symbolic links from a folder ($CIFTIFY_WORKDIR/zz_templates) to the
subject's output folder. If the --no-symlinks flag is indicated, these files will be
copied into the subject folder insteadself.

Written by Erin W Dickie
"""

import re
import sys
import docopt as dcpt
import simplejson as json
from argparse import ArgumentParser


class docoptHelper():

    def __init__(self):
        self.descriptor = {}

        self.positional_arguments = {}
        self.optional_arguments = {}
        self.dcpt_cmdl = ""
        self.dcpt_args = ""
        self.dcpt_opts = ""
        self.descriptions = ""
        self.help = ""

    def importDocopt(self, docopt_str):
        # initial doc validation
        extc_dict = dcpt.docopt(docopt_str)

        self.dcpt_cmdl = dcpt.parse_section('usage:', docopt_str)
        self.dcpt_args = dcpt.parse_section('arguments:', docopt_str)
        self.dcpt_opts = dcpt.parse_section('options:', docopt_str)

        options = dcpt.parse_defaults(docopt_str)
        pattern = dcpt.parse_pattern(
            dcpt.formal_usage(self.dcpt_cmdl[0]), options)
        argv = dcpt.parse_argv(dcpt.Tokens(sys.argv[1:]), list(options), False)
        pattern_options = set(pattern.flat(dcpt.Option))
        for options_shortcut in pattern.flat(dcpt.OptionsShortcut):
            doc_options = dcpt.parse_defaults(docopt_str)
            options_shortcut.children = list(set(doc_options) - pattern_options)
        matched, left, collected = pattern.fix().match(argv)

        # can loop through to compare extracted params with extc_dict
        # and add param to argparser for each prm
        for prm in pattern.flat():
            if type(prm) is dcpt.Argument:
                self.positional_arguments[prm.name] = {"value": prm.value}
            elif type(prm) is dcpt.Option:
                self.optional_arguments[prm.name] = \
                    {"value": prm.value,
                     "short": prm.short,
                     "long:": prm.long,
                     "argcount": prm.argcount}
            else:
                raise EnvironmentError(
                    "Unrecognized argument of type {0}\n\"{1}\": {2}".format(
                        type(prm), prm.name, prm.value))

    def extractCommandLine(self):
        self.descriptor["command-line"] = self.dcpt_cmdl[0].split()[1]

        # Match params in command line with extracted pos_args
        for arg in self.dcpt_cmdl[0].split()[2:]:
            if arg == "[options]":
                for opt in [opt[2:] for opt in self.optional_arguments]:
                    self.descriptor["command-line"] += \
                        " [{0}]".format(opt.upper())
            elif arg[1:-1] in [prm[1:-1] for prm in self.positional_arguments]:
                self.descriptor["command-line"] += \
                    " [{0}]".format(arg.upper()[1:-1])
            else:
                print("{0} not added to command line".format(arg))

    def extractDescription(self):
        self.descriptions = __doc__ \
            .replace("".join(self.dcpt_cmdl), "") \
            .replace("".join(self.dcpt_args), "") \
            .replace("".join(self.dcpt_opts), "")
        self.descriptor["description"] = self.descriptions

    def extractInputs(self):
        self.descriptor["inputs"] = []
        for inp in [inp[1:-1] for inp in self.positional_arguments]:
            newInp = {
                "id": inp,
                "name": inp.replace("_", " "),
                "optional": "TODO",
                "type": "TODO",
                "value-key": "[{0}]".format(inp.upper())
            }
            self.descriptor["inputs"].append(newInp)

    def generateDescriptor(self):
        self.importDocopt(__doc__)
        self.extractCommandLine()
        self.extractDescription()
        self.extractInputs()

        print(json.dumps(self.descriptor, indent=4))

docoptHelper().generateDescriptor()
