'''
BOUTIQUES COMMANDS

TOOL CREATION
* create: create a Boutiques descriptor from scratch.
* export: export a descriptor to other formats.
* import: create a descriptor for a BIDS app or update a descriptor from \
an older version of the schema. Options: "bids", "0.4", "cwl", "docopt"
* validate: validate an existing boutiques descriptor.

TOOL USAGE & EXECUTION
* example: generate example command-line for descriptor.
* pprint: generate pretty help text from a descriptor.
* exec: launch or simulate an execution given a descriptor and a set of inputs.
* test: run pytest on a descriptor detailing tests.

TOOL SEARCH & PUBLICATION
* deprecate: deprecate a published tool. The tool will still be published and
usable, but it won't show in search results.
* publish: create an entry in Zenodo for the descriptor and adds the DOI \
created by Zenodo to the descriptor.
* pull: download a descriptor from Zenodo.
* search: search Zenodo for descriptors.

DATA COLLECTION
* data: manage execution data collection.

OTHER
* evaluate: given an invocation and a descriptor,queries execution properties.
* invocation: generate or validate inputs against the invocation schema
* for a given descriptor.
* version: print the Boutiques version.
'''

import os
import simplejson as json
from argparse import ArgumentParser, RawTextHelpFormatter


def add_subparser_create(subparsers):
    parser_create = subparsers.add_parser(
        "create", description="Boutiques descriptor creator")
    parser_create.set_defaults(function='create')
    parser_create.add_argument("descriptor", action="store",
                               help="Output file to store descriptor in.")
    parser_create.add_argument("--docker-image", '-d', action="store",
                               help="Name of Docker image on DockerHub.")
    parser_create.add_argument("--use-singularity", '-u', action="store_true",
                               help="When --docker-image is used. Specify to "
                               "use singularity to run it.")
    parser_create.add_argument(
        "--cl-template", action="store",
        help="Command-line template used to generate"
        " descriptor inputs. (Path to descriptor or String)")
    parser_create.add_argument(
        "--camel-case",
        action="store_true",
        help="All input IDs will be written in camelCase.")


def add_subparser_data(subparsers):
    parser_data = subparsers.add_parser(
        "data", description="Manage execution data collection.")
    parser_data.set_defaults(function='data')
    data_subparsers = parser_data.add_subparsers(
        help="Manage execution data records. Inspect: displays "
        "the unpublished records currently in the cache. "
        "Publish: publishes contents of cache to Zenodo as "
        "a public data set. Requires a Zenodo access token, "
        "see http://developers.zenodo.org/#authentication. "
        "Delete: remove one or more records from the cache.")

    parser_data_delete = data_subparsers.add_parser(
        "delete", description="Delete data record(s) in cache.")
    parser_data_delete.set_defaults(mode='delete')
    parser_data_delete.add_argument("-f", "--file", action="store",
                                    help="Filename of record to delete.")
    parser_data_delete.add_argument("--no-int", '-y', action="store_true",
                                    help="disable interactive input.")

    parser_data_inspect = data_subparsers.add_parser(
        "inspect", description="Displays contents of cache")
    parser_data_inspect.set_defaults(mode='inspect')
    parser_data_inspect.add_argument("-e", "--example", action="store_true",
                                     help="Display example data file contents.")

    parser_data_publish = data_subparsers.add_parser(
        "publish", description="Publishes record(s) to a data set.")
    parser_data_publish.set_defaults(mode='publish')
    parser_data_publish.add_argument(
        "-a",
        "--author",
        action="store",
        help="Set the author name for the data set "
        "publication. Defaults to anonymous.")
    parser_data_publish.add_argument(
        "-f",
        "--file",
        action="store",
        help="Filename of record to publish alone as a "
        "data set.")
    parser_data_publish.add_argument(
        "-i",
        "--individually",
        action="store_true",
        help="Publishes all data files in cache as "
        "independent data sets, By Default will publish "
        "files in bulk data sets.")
    parser_data_publish.add_argument("--no-int", '-y', action="store_true",
                                     help="disable interactive input.")
    parser_data_publish.add_argument("-v", "--verbose", action="store_true",
                                     help="print information messages.")
    parser_data_publish.add_argument(
        "--sandbox",
        action="store_true",
        help="publish to Zenodo's sandbox instead of "
        "production server. Recommended for tests.")
    parser_data_publish.add_argument(
        "--zenodo-token",
        action="store",
        help="Zenodo API token to use for authentication. "
        "If not used, token will be read from "
        "configuration file or requested interactively.")
    parser_data_publish.add_argument("--nexus", action="store_true",
                                     help="Publish to Nexus instead of Zenodo. "
                                     "Sandbox URL is "
                                     "https://sandbox.bluebrainnexus.io")
    parser_data_publish.add_argument(
        "--nexus-token",
        action="store",
        help="Nexus API token to use for authentication. ")
    parser_data_publish.add_argument("--nexus-org", action="store",
                                     help="Nexus organization to publish to. ")
    parser_data_publish.add_argument("--nexus-project", action="store",
                                     help="Nexus project to publish to. ")


def add_subparser_deprecate(subparsers):
    parser_deprecate = subparsers.add_parser(
        "deprecate", description="Deprecates a published descriptor by"
        " creating a new version with the 'deprecated' tag"
        " on Zenodo. The descriptor remains available from"
        " its Zenodo id, but it won't show in search"
        " results. This works by creating a new version of"
        " the tool in Zenodo, marked with keyword"
        " 'deprecated'.")
    parser_deprecate.set_defaults(function='deprecate')
    parser_deprecate.add_argument("zid", action="store", help="Zenodo id "
                                  "of the descriptor to deprecate, "
                                  "prefixed by 'zenodo.', e.g. zenodo.123456")
    parser_deprecate.add_argument(
        "--by", action="store", help="Zenodo id (e.g., "
        "zenodo-1234) of a  descriptor that will supersede "
        "the deprecated one.")
    parser_deprecate.add_argument(
        "--zenodo-token",
        action="store",
        help="Zenodo API token to use for authentication. "
        "If not used, token will be read from configuration "
        "file or requested interactively.")
    parser_deprecate.add_argument("-v", "--verbose", action="store_true",
                                  help="Print information messages")
    parser_deprecate.add_argument("--sandbox", action="store_true",
                                  help="use Zenodo's sandbox instead of "
                                  "production server. Recommended for tests.")


def add_subparser_evaluate(subparsers):
    parser_evaluate = subparsers.add_parser(
        "evaluate", description="Evaluates parameter values for a"
        " descriptor and invocation")
    parser_evaluate.set_defaults(function='evaluate')
    parser_evaluate.add_argument(
        "descriptor",
        action="store",
        help="The Boutiques descriptor as a JSON file, JSON "
        "string or Zenodo ID (prefixed by 'zenodo.').")
    parser_evaluate.add_argument("invocation", action="store",
                                 help="Input JSON complying to invocation.")
    parser_evaluate.add_argument(
        "query",
        action="store",
        nargs="*",
        help="The query to be performed. Simply request keys "
        "from the descriptor (i.e. output-files), and chain "
        "together queries (i.e. id=myfile or optional=false) "
        "slashes between them and commas connecting them. "
        "(i.e. output-files/optional=false,id=myfile). "
        "Perform multiple queries by separating them with a "
        "space.")
    parser_evaluate.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")


def add_subparser_example(subparsers):
    parser_example = subparsers.add_parser(
        "example",
        description="Generates example invocation from a"
        " valid descriptor")
    parser_example.set_defaults(function='example')
    parser_example.add_argument(
        "descriptor",
        action="store",
        help="The Boutiques descriptor as a JSON file, "
        "JSON string or Zenodo ID (prefixed by 'zenodo.').")
    parser_example.add_argument("-c", "--complete", action="store_true",
                                help="Include optional parameters.")
    parser_example.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")


def add_subparser_execute(subparsers):
    parser_exec = subparsers.add_parser(
        "exec", description="Boutiques local executor")
    parser_exec.set_defaults(function='exec')
    exec_subparsers = parser_exec.add_subparsers(
        help="Mode of operation to use. Launch: takes a "
        "set of inputs compliant with invocation schema "
        "and launches the tool. Simulate: shows sample "
        "command-lines based on the provided descriptor"
        " based on provided or randomly generated inputs. "
        "Prepare: pulls the Docker or Singularity container "
        "image for a given descriptor. ")

    parser_exec_launch = exec_subparsers.add_parser(
        "launch", description="Launches an invocation.")
    parser_exec_launch.set_defaults(mode='launch')
    parser_exec_launch.add_argument(
        "descriptor",
        action="store",
        help="The Boutiques descriptor as a JSON file, "
        "JSON string or Zenodo ID (prefixed by 'zenodo.').")
    parser_exec_launch.add_argument("invocation", action="store",
                                    help="Input JSON complying to invocation.")
    parser_exec_launch.add_argument(
        "-v",
        "--volumes",
        action="append",
        type=str,
        help="Volumes to mount when launching the "
        "container. Format consistently the following:"
        " /a:/b will mount local directory /a to "
        "container directory /b.")
    parser_exec_launch.add_argument("-x", "--debug", action="store_true",
                                    help="Keeps temporary scripts used during "
                                    "execution, and prints additional debug "
                                    "messages.")
    parser_exec_launch.add_argument(
        "-u",
        "--user",
        action="store_true",
        help="Runs the container as local user ({0})"
        " instead of root.".format(
            os.getenv("USER")))
    parser_exec_launch.add_argument(
        "-s",
        "--stream",
        action="store_true",
        help="Streams stdout and stderr in real time "
        "during execution.")
    parser_exec_launch.add_argument(
        "--imagepath", action="store", help="Path to Singularity image. "
        "If not specified, will use current directory.")
    parser_exec_launch.add_argument(
        "--skip-data-collection",
        action="store_true",
        help="Skips execution data collection and saving"
        "to cache.")
    parser_exec_launch.add_argument(
        "--provenance",
        action="store",
        type=json.loads,
        help="Append JSON object to the generated record.")
    parser_exec_launch.add_argument(
        "--no-container",
        action="store_true",
        help="Launch invocation on the host computer, with "
        "no container. If 'container-image' appears in the "
        "descriptor, it is ignored.")
    parser_exec_launch.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")
    parser_exec_launch.add_argument(
        "--no-automounts",
        action="store_true",
        help="Disable automatic mount of all input files "
        "present in the invocation")
    force_group = parser_exec_launch.add_mutually_exclusive_group()
    force_group.add_argument("--force-docker", action="store_true",
                             help="Tries to run Singularity images with "
                             "Docker. This only works if the image is on"
                             "Docker Hub, i.e. has index docker://")
    force_group.add_argument("--force-singularity", action="store_true",
                             help="Tries to run Docker images with "
                             "Singularity.")

    parser_exec_prepare = exec_subparsers.add_parser(
        "prepare",
        description="Pulls the container image for a given descriptor")
    parser_exec_prepare.set_defaults(mode='prepare')
    parser_exec_prepare.add_argument(
        "descriptor",
        action="store",
        help="The Boutiques descriptor as a JSON file, "
        "JSON string or Zenodo ID (prefixed by 'zenodo.').")
    parser_exec_prepare.add_argument("-x", "--debug", action="store_true",
                                     help="Keeps temporary scripts used during "
                                     "execution, and prints additional debug "
                                     "messages.")
    parser_exec_prepare.add_argument(
        "-s",
        "--stream",
        action="store_true",
        help="Streams stdout and stderr in real time "
        "during execution.")
    parser_exec_prepare.add_argument(
        "--imagepath", action="store", help="Path to Singularity image. "
        "If not specified, will use current directory.")
    parser_exec_prepare.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")

    parser_exec_simulate = exec_subparsers.add_parser(
        "simulate", description="Simulates an invocation.")
    parser_exec_simulate.set_defaults(mode='simulate')
    parser_exec_simulate.add_argument(
        "descriptor",
        action="store",
        help="The Boutiques descriptor as a JSON file, "
        "JSON string or Zenodo ID (prefixed by 'zenodo.').")
    parser_exec_simulate.add_argument(
        "-i",
        "--input",
        action="store",
        help="Input JSON complying to invocation.")
    parser_exec_simulate.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Flag to generate invocation in JSON format.")
    parser_exec_simulate.add_argument("-c", "--complete", action="store_true",
                                      help="Include optional parameters.")
    parser_exec_simulate.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")


def add_subparser_export(subparsers):
    parser_export = subparsers.add_parser(
        "export", description="Export Boutiques descriptor to"
        " other formats.")
    parser_export.set_defaults(function='export')
    parser_export.add_argument("type", help="Type of export we are performing.",
                               choices=["carmin"])
    parser_export.add_argument(
        "descriptor", help="Boutiques descriptor to export.")
    parser_export.add_argument("--identifier", help="Identifier to use in"
                               "CARMIN export.")
    parser_export.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")
    parser_export.add_argument("output", help="Output file where to write the"
                               " converted descriptor.")


def add_subparser_import(subparsers):
    parser_import = subparsers.add_parser(
        "import", description="Imports old descriptor or BIDS app or"
        " CWL descriptor or docopt script to spec.")
    parser_import.set_defaults(function='import')
    parser_import.add_argument(
        "type", help="Type of import we are performing. Allowed values: {0}"
        .format(", ".join(["bids", "0.4", "cwl", "docopt", "config"])),
        choices=["bids", "0.4", "cwl", "docopt", "config"],
        metavar='type')
    parser_import.add_argument("output_descriptor", help="Where the Boutiques"
                               " descriptor will be written.")
    parser_import.add_argument("input_descriptor", help="Input descriptor to be"
                               " converted. For '0.4', is JSON descriptor,"
                               " for 'docopt' is Docopt script,"
                               " for 'bids' is base directory of BIDS app,"
                               " for 'cwl' is YAML descriptor."
                               " for 'config' is configuration file"
                               " {.json, .toml, .yml}.)")
    parser_import.add_argument(
        "-o",
        "--output-invocation",
        help="Where to write "
        "the invocation if any.")
    parser_import.add_argument(
        "-i",
        "--input-invocation",
        help="Input invocation "
        " for CWL if any.")


def add_subparser_invocation(subparsers):
    parser_invocation = subparsers.add_parser(
        "invocation", description="Creates invocation schema and"
        " validates invocations. Uses descriptor's"
        " invocation schema if it exists, otherwise"
        " creates one.")
    parser_invocation.set_defaults(function='invocation')
    parser_invocation.add_argument(
        "descriptor",
        action="store",
        help="The Boutiques descriptor as a JSON file, JSON "
        "string or Zenodo ID (prefixed by 'zenodo.').")
    parser_invocation.add_argument(
        "-i",
        "--invocation",
        action="store",
        help="Input values in a JSON file or as a JSON "
        "object to be validated against "
        "the invocation schema.")
    parser_invocation.add_argument(
        "-w",
        "--write-schema",
        action="store_true",
        help="If descriptor doesn't have an invocation "
        "schema, creates one and writes it to the descriptor"
        " file ")
    parser_invocation.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")


def add_subparser_pprint(subparsers):
    parser_pprint = subparsers.add_parser(
        "pprint", description="Boutiques pretty-print for"
        "generating help text")
    parser_pprint.set_defaults(function='pprint')
    parser_pprint.add_argument("descriptor", action="store",
                               help="The Boutiques descriptor.")
    parser_pprint.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")


def add_subparser_publish(subparsers):
    parser_publish = subparsers.add_parser(
        "publish", description="A publisher of Boutiques tools"
        " in Zenodo (http://zenodo.org). Requires "
        "a Zenodo access token, see "
        "http://developers.zenodo.org/#authentication.")
    parser_publish.set_defaults(function='publish')
    parser_publish.add_argument("boutiques_descriptor", action="store",
                                help="local path of the "
                                " Boutiques descriptor to publish.")
    parser_publish.add_argument("--sandbox", action="store_true",
                                help="publish to Zenodo's sandbox instead of "
                                "production server. Recommended for tests.")
    parser_publish.add_argument(
        "--zenodo-token",
        action="store",
        help="Zenodo API token to use for authentication. "
        "If not used, token will be read from configuration "
        "file or requested interactively.")
    parser_publish.add_argument("--no-int", '-y', action="store_true",
                                help="disable interactive input.")
    parser_publish.add_argument("-v", "--verbose", action="store_true",
                                help="print information messages.")
    publish_mutex_group = parser_publish.add_mutually_exclusive_group()
    publish_mutex_group.add_argument(
        "-r",
        "--replace",
        action="store_true",
        help="Publish an updated version of an existing "
        "record. The descriptor must contain a DOI, which "
        "will be replaced with a new one.")
    publish_mutex_group.add_argument(
        "--id",
        action="store",
        help="Zenodo ID of an existing record you wish to "
        "update with a new version, prefixed by "
        "'zenodo.' (e.g. zenodo.123456).")


def add_subparser_pull(subparsers):
    parser_pull = subparsers.add_parser(
        "pull", description="Ensures that Zenodo descriptors are"
        " locally cached, downloading them if needed.")
    parser_pull.set_defaults(function='pull')
    parser_pull.add_argument("zids", nargs="+", action="store", help="One or "
                             "more Zenodo IDs for the descriptor(s) to pull, "
                             "prefixed by 'zenodo.', e.g. zenodo.123456 "
                             "zenodo.123457")
    parser_pull.add_argument("-v", "--verbose", action="store_true",
                             help="Print information messages")
    parser_pull.add_argument("--sandbox", action="store_true",
                             help="pull from Zenodo's sandbox instead of "
                             "production server. Recommended for tests.")


def add_subparser_search(subparsers):
    parser_search = subparsers.add_parser(
        "search", description="Search Zenodo for Boutiques"
        " descriptors. When no term is supplied, will"
        " search for all descriptors.", )
    parser_search.set_defaults(function='search')
    parser_search.add_argument("query", nargs="?", default="boutiques",
                               action="store", help="Search query")
    parser_search.add_argument("-v", "--verbose", action="store_true",
                               help="Print information messages")
    parser_search.add_argument("--sandbox", action="store_true",
                               help="search Zenodo's sandbox instead of "
                               "production server. Recommended for tests.")
    parser_search.add_argument("-m", "--max", action="store", type=int,
                               help="Specify the maximum number of results "
                               "to be returned. Default is 10.")
    parser_search.add_argument("-nt", "--no-trunc", action="store_true",
                               help="Do not truncate long tool descriptions.")
    parser_search.add_argument(
        "-e",
        "--exact",
        action="store_true",
        help="Only return results containing the exact query.")


def add_subparser_test(subparsers):
    parser_test = subparsers.add_parser(
        "test", description="Perform all the tests defined within"
        " the given descriptor")
    parser_test.set_defaults(function='test')
    parser_test.add_argument(
        "descriptor",
        action="store",
        help="The Boutiques descriptor as a JSON file, JSON "
        "string or Zenodo ID (prefixed by 'zenodo.').")
    parser_test.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")
    parser_test.add_argument("--imagepath", action="store",
                             help="Path to Singularity image. "
                             "If not specified, will use current directory.")


def add_subparser_validate(subparsers):
    parser_validate = subparsers.add_parser(
        "validate", description="Boutiques descriptor validator")
    parser_validate.set_defaults(function='validate')
    parser_validate.add_argument(
        "descriptor",
        action="store",
        help="The Boutiques descriptor as a JSON file, JSON "
        "string or Zenodo ID (prefixed by 'zenodo.').")
    parser_validate.add_argument(
        "--bids",
        "-b",
        action="store_true",
        help="Flag indicating if descriptor is a BIDS app")
    parser_validate.add_argument(
        "--format",
        "-f",
        action="store_true",
        help="If descriptor is valid, rewrite it with sorted"
        " keys.")
    parser_validate.add_argument(
        "--sandbox",
        action="store_true",
        help="Get descriptor from Zenodo's sandbox instead of "
        "production server.")


def add_subparser_version(subparsers):
    parser_version = subparsers.add_parser(
        "version", description="Print the Boutiques version.")
    parser_version.set_defaults(function='version')


def parser_bosh():
    parser = ArgumentParser(add_help=False,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("--help", "-h", action="store_true",
                        help="show this help message and exit")
    subparsers = parser.add_subparsers(help=__doc__)
    add_subparser_create(subparsers)
    add_subparser_data(subparsers)
    add_subparser_deprecate(subparsers)
    add_subparser_evaluate(subparsers)
    add_subparser_example(subparsers)
    add_subparser_execute(subparsers)
    add_subparser_export(subparsers)
    add_subparser_import(subparsers)
    add_subparser_invocation(subparsers)
    add_subparser_pprint(subparsers)
    add_subparser_publish(subparsers)
    add_subparser_pull(subparsers)
    add_subparser_search(subparsers)
    add_subparser_test(subparsers)
    add_subparser_validate(subparsers)
    add_subparser_version(subparsers)
    return parser
