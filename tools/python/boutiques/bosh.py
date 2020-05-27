#!/usr/bin/env python

import jsonschema
import simplejson as json
import os
import sys
import os.path as op
import tempfile
import pytest
from argparse import ArgumentParser, RawTextHelpFormatter
from jsonschema import ValidationError
from boutiques.validator import DescriptorValidationError
from boutiques.publisher import ZenodoError
from boutiques.nexusHelper import NexusError
from boutiques.invocationSchemaHandler import InvocationValidationError
from boutiques.localExec import ExecutorOutput
from boutiques.localExec import ExecutorError
from boutiques.exporter import ExportError
from boutiques.importer import ImportError
from boutiques.localExec import addDefaultValues
from boutiques.util.utils import loadJson, customSortInvocationByInput
from boutiques.logger import raise_error
from tabulate import tabulate


def pprint(*params):
    parser = parser_bosh()
    params = ('pprint',) + params
    results = parser.parse_args(params)

    from boutiques.prettyprint import PrettyPrinter
    desc = loadJson(results.descriptor, sandbox=results.sandbox)
    prettyclass = PrettyPrinter(desc)
    return prettyclass.docstring


def create(*params):
    parser = parser_bosh()
    params = ('create',) + params
    results = parser.parse_args(params)

    from boutiques.creator import CreateDescriptor
    new = CreateDescriptor(parser=None,
                           docker_image=results.docker_image,
                           use_singularity=results.use_singularity,
                           camel_case=results.camel_case)
    new.save(results.descriptor)
    return None


def validate(*params):
    parser = parser_bosh()
    params = ('validate',) + params
    results = parser.parse_args(params)

    from boutiques.validator import validate_descriptor
    descriptor = validate_descriptor(results.descriptor,
                                     format_output=results.format,
                                     sandbox=results.sandbox)
    if results.bids:
        from boutiques.bids import validate_bids
        validate_bids(descriptor, valid=True)


def execute(*params):
    parser = parser_bosh()
    helps = any([True for ht in ["--help", "-h"] if ht in params])
    if (len(params) <= 1 and helps) or isinstance(params[0], list):
        parser.print_help()
        raise SystemExit

    params = ('exec',) + params
    args, params = parser.parse_known_args(params)
    mode = args.mode
    params += ["--help"] if args.help is True else []
    results = args

    if mode == "launch":
        descriptor = results.descriptor
        inp = results.invocation

        # Validate invocation and descriptor
        arguments = [descriptor, '-i', inp]
        if results.sandbox:
            arguments.append('--sandbox')
        valid = invocation(*arguments)

        # Generate object that will perform the commands
        from boutiques.localExec import LocalExecutor
        executor = LocalExecutor(descriptor, inp,
                                 {"forcePathType": True,
                                  "debug": results.debug,
                                  "changeUser": results.user,
                                  "stream": results.stream,
                                  "imagePath": results.imagepath,
                                  "skipDataCollect":
                                      results.skip_data_collection,
                                  "forceDocker": results.force_docker,
                                  "forceSingularity":
                                      results.force_singularity,
                                  "provenance": results.provenance,
                                  "noContainer": results.no_container,
                                  "sandbox": results.sandbox})
        # Execute it
        return executor.execute(results.volumes)

    if mode == "simulate":
        descriptor = results.descriptor

        # Do some basic input scrubbing
        inp = results.input

        arguments = [descriptor]
        if inp:
            arguments.append('-i')
            arguments.append(inp)
        if results.sandbox:
            arguments.append('--sandbox')
        valid = invocation(*arguments)

        # Generate object that will perform the commands
        from boutiques.localExec import LocalExecutor
        executor = LocalExecutor(descriptor, inp,
                                 {"forcePathType": True,
                                  "destroyTempScripts": True,
                                  "changeUser": True,
                                  "skipDataCollect": True,
                                  "requireComplete": results.complete,
                                  "sandbox": results.sandbox})
        if not inp:
            # Add optional inputs with default-value to inputs_dict,
            # which is then populated with random params
            executor.in_dict = addDefaultValues(executor.desc_dict, {})
            executor.generateRandomParams(generateCmdLineFromInDict=True)

        if results.json:
            sout = [json.dumps(
                customSortInvocationByInput(executor.in_dict, descriptor),
                indent=4)]
            print(sout[0])
        else:
            executor.printCmdLine()
            sout = executor.cmd_line

        # for consistency with execute
        # Adding hide to "container location" field since it's an invalid
        # value, can parse that to hide the summary print
        return ExecutorOutput(os.linesep.join(sout), "",
                              0, "", [], [], os.linesep.join(sout), "", "hide")

    if mode == "prepare":
        descriptor = results.descriptor

        # Validate descriptor
        arguments = [descriptor]
        if results.sandbox:
            arguments.append('--sandbox')
        valid = invocation(*arguments)

        # Generate object that will perform the commands
        from boutiques.localExec import LocalExecutor
        executor = LocalExecutor(descriptor, None,
                                 {"forcePathType": True,
                                  "debug": results.debug,
                                  "stream": results.stream,
                                  "imagePath": results.imagepath,
                                  "skipDataCollect": True,
                                  "sandbox": results.sandbox})
        container_location = executor.prepare()[1]
        print("Container location: " + container_location)

        # Adding hide to "container location" field since it's an invalid
        # value, and we can parse that to hide the summary print
        return ExecutorOutput(container_location, "",
                              0, "", [], [], "", "", "hide")


def importer(*params):
    parser = parser_bosh()
    params = ('import',) + params
    results = parser.parse_args(params)

    from boutiques.importer import Importer
    importer = Importer(results.input_descriptor,
                        results.output_descriptor,
                        results.input_invocation,
                        results.output_invocation)
    if results.type == "0.4":
        importer.upgrade_04()
    elif results.type == "bids":
        importer.import_bids()
    elif results.type == "cwl":
        importer.import_cwl()
    elif results.type == "docopt":
        create(results.output_descriptor)
        importer.import_docopt(results.output_descriptor)


def exporter(*params):
    parser = parser_bosh()
    params = ('export',) + params
    results = parser.parse_args(params)

    descriptor = results.descriptor
    output = results.output

    args = [results.descriptor]
    if results.sandbox:
        args.append("--sandbox")
    validate(*args)

    from boutiques.exporter import Exporter
    exporter = Exporter(descriptor, results.identifier,
                        sandbox=results.sandbox)
    if results.type == "carmin":
        exporter.carmin(output)


def publish(*params):
    parser = parser_bosh()
    params = ('publish',) + params
    results = parser.parse_args(params)

    from boutiques.publisher import Publisher
    publisher = Publisher(results.boutiques_descriptor,
                          results.zenodo_token,
                          results.verbose,
                          results.sandbox,
                          results.no_int,
                          results.replace,
                          results.id)
    publisher.publish()
    if hasattr(publisher, 'doi'):
        return publisher.doi


def invocation(*params):
    parser = parser_bosh()
    params = ('invocation',) + params
    results = parser.parse_args(params)
    arguments = [results.descriptor]
    if results.sandbox:
        arguments.append('--sandbox')
    validate(*arguments)
    descriptor = loadJson(results.descriptor, sandbox=results.sandbox)
    if descriptor.get("invocation-schema"):
        invSchema = descriptor.get("invocation-schema")
    else:
        from boutiques.invocationSchemaHandler import generateInvocationSchema
        invSchema = generateInvocationSchema(descriptor)
        if results.write_schema:
            descriptor["invocation-schema"] = invSchema
            with open(results.descriptor, "w") as f:
                f.write(json.dumps(descriptor, indent=4))
    if results.invocation:
        from boutiques.invocationSchemaHandler import validateSchema
        data = addDefaultValues(descriptor, loadJson(results.invocation))
        validateSchema(invSchema, data)


def evaluate(*params):
    parser = parser_bosh()
    params = ('evaluate',) + params
    results = parser.parse_args(params)

    # Generate object that will parse the invocation and descriptor
    from boutiques.localExec import LocalExecutor
    executor = LocalExecutor(results.descriptor, results.invocation,
                             {"forcePathType": True,
                              "destroyTempScripts": True,
                              "changeUser": True,
                              "skipDataCollect": True,
                              "sandbox": results.sandbox})

    from boutiques.evaluate import evaluateEngine
    query_results = []
    for query in results.query:
        query_results += [evaluateEngine(executor, query)]
    return query_results[0] if len(query_results) == 1 else query_results


def test(*params):
    parser = parser_bosh()
    params = ('test',) + params
    results = parser.parse_args(params)

    args = [results.descriptor]
    if results.sandbox:
        args.append("--sandbox")

    # Generation of the invocation schema (and descriptor validation).
    invocation(*args)

    # Extraction of all the invocations defined for the test-cases.
    descriptor = loadJson(results.descriptor, sandbox=results.sandbox)

    if (not descriptor.get("tests")):
        # If no tests have been specified, we consider testing successful.
        return 0

    for test in descriptor["tests"]:
        invocation_JSON = test["invocation"]

        testArgs = [results.descriptor, "--invocation",
                    json.dumps(invocation_JSON)]
        if results.sandbox:
            testArgs.append("--sandbox")
        # Check if the invocation is valid.
        invocation(*testArgs)

    # Invocations have been properly validated. We can launch the actual tests.
    test_path = op.join(op.dirname(op.realpath(__file__)), "test.py")
    test_args = [test_path, "--descriptor", results.descriptor]
    if results.imagepath:
        test_args.extend(["--imagepath", results.imagepath])
    return pytest.main(args=test_args)


def search(*params):
    parser = parser_bosh()
    params = ('search',) + params
    results = parser.parse_args(params)

    from boutiques.searcher import Searcher
    searcher = Searcher(results.query, results.verbose, results.sandbox,
                        results.max, results.no_trunc, results.exact)

    return searcher.search()


def example(*params):
    parser = parser_bosh()
    params = ('example',) + params
    results = parser.parse_args(params)

    descriptor = results.descriptor
    arguments = [descriptor]
    if results.sandbox:
        arguments.append('--sandbox')
    valid = invocation(*arguments)

    # Generate object that will perform the commands
    from boutiques.localExec import LocalExecutor
    executor = LocalExecutor(descriptor, None,
                             {"forcePathType": True,
                              "destroyTempScripts": True,
                              "changeUser": True,
                              "skipDataCollect": True,
                              "requireComplete": results.complete,
                              "sandbox": results.sandbox})
    executor.generateRandomParams()
    return json.dumps(
        customSortInvocationByInput(executor.in_dict, descriptor), indent=4)


def pull(*params):
    parser = parser_bosh()
    params = ('pull',) + params
    results = parser.parse_args(params)

    from boutiques.puller import Puller
    puller = Puller(results.zids, results.verbose, results.sandbox)
    return puller.pull()


def data(*params):
    parser = parser_bosh()
    helps = any([True for ht in ["--help", "-h"] if ht in params])

    if (len(params) <= 1 and helps) or isinstance(params[0], list):
        parser.print_help()
        raise SystemExit

    params = ('data',) + params
    args, params = parser.parse_known_args(params)
    action = args.mode
    params += ["--help"] if args.help is True else []
    results = args

    if action == "inspect":
        from boutiques.dataHandler import DataHandler
        dataHandler = DataHandler()
        return dataHandler.inspect(results.example)

    if action == "publish":
        from boutiques.dataHandler import DataHandler
        dataHandler = DataHandler()
        return dataHandler.publish(results.file, results.zenodo_token,
                                   results.author, results.nexus_token,
                                   results.nexus_org, results.nexus_project,
                                   results.individually, results.sandbox,
                                   results.no_int, results.verbose,
                                   results.nexus)

    if action == "delete":
        from boutiques.dataHandler import DataHandler
        dataHandler = DataHandler()
        return dataHandler.delete(results.file, results.no_int)


def deprecate(*params):
    parser = parser_bosh()
    params = ('deprecate',) + params
    result = parser.parse_args(params)

    from boutiques.deprecate import deprecate
    return deprecate(result.zid, by_zenodo_id=result.by,
                     sandbox=result.sandbox, verbose=result.verbose,
                     zenodo_token=result.zenodo_token)


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
    parser_import.add_argument("type", help="Type of import we are performing."
                               " Allowed values: {" +
                               ", ".join(
                                   ["bids", "0.4", "cwl", "docopt"]) + "}",
                               choices=["bids", "0.4", "cwl", "docopt"],
                               metavar='type')
    parser_import.add_argument("output_descriptor", help="Where the Boutiques"
                               " descriptor will be written.")
    parser_import.add_argument("input_descriptor", help="Input descriptor to be"
                               " converted. For '0.4', is JSON descriptor,"
                               " for 'docopt' is JSON descriptor,"
                               " for 'bids' is base directory of BIDS app,"
                               " for 'cwl' is YAML descriptor.")
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
    helptext = r'''
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
    parser.add_argument("--help", "-h", action="store_true",
                        help="show this help message and exit")
    subparsers = parser.add_subparsers(help=helptext)
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


def bosh(args=None):
    # Returns True if bosh was called from the CLI
    def runs_as_cli():
        return os.path.basename(sys.argv[0]) == "bosh"

    def bosh_return(val, code=0, hide=False, formatted=None):
        if runs_as_cli():
            if hide:
                return code
            if val is not None:
                if formatted is not None:
                    print(formatted)
                else:
                    print(val)
            else:
                if code == 0:
                    print("OK")
                else:
                    print("Failed")
            return code  # everything went well
        return val  # calling function wants this value

    # Params are set depending on where bosh is called from
    if runs_as_cli():
        params = sys.argv[2:] if len(sys.argv) > 2 else []
        func = sys.argv[1] if len(sys.argv) > 1 else sys.argv
    else:
        params = args[1:] if len(args) > 1 else []
        func = args[0] if len(args) > 0 else args

    try:
        if func == "create":
            out = create(*params)
            return bosh_return(out, hide=True)
        elif func == "validate":
            out = validate(*params)
            return bosh_return(out)
        elif func == "exec":
            out = execute(*params)
            # If executed through CLI, print 'out' and return exit_code
            # Otherwise, return out
            return bosh_return(out, out.exit_code,
                               hide=bool(out.container_location == 'hide'))
        elif func == "example":
            out = example(*params)
            return bosh_return(out)
        elif func == "import":
            out = importer(*params)
            return bosh_return(out)
        elif func == "export":
            out = exporter(*params)
            return bosh_return(out)
        elif func == "publish":
            out = publish(*params)
            return bosh_return(out)
        elif func == "invocation":
            out = invocation(*params)
            return bosh_return(out)
        elif func == "evaluate":
            out = evaluate(*params)
            return bosh_return(out)
        elif func == "test":
            out = test(*params)
            return bosh_return(out)
        elif func == "pprint":
            out = pprint(*params)
            return bosh_return(out)
        elif func == "search":
            out = search(*params)
            return bosh_return(out, formatted=tabulate(out, headers='keys',
                                                       tablefmt='plain'))
        elif func == "pull":
            out = pull(*params)
            return bosh_return(out, hide=True)
        elif func == "data":
            out = data(*params)
            return bosh_return(out)
        elif func == "version":
            from boutiques.__version__ import VERSION
            return bosh_return(VERSION)
        elif func == "deprecate":
            out = deprecate(*params)
            return bosh_return(out)
        else:
            parser_bosh().print_help()
            raise SystemExit

    except (ZenodoError,
            NexusError,
            DescriptorValidationError,
            InvocationValidationError,
            ValidationError,
            ExportError,
            ImportError,
            ExecutorError) as e:
        # We don't want to raise an exception when function is called
        # from CLI.'
        if runs_as_cli():
            print(e)
            return 99  # Note: this conflicts with tool error codes.
        raise e


bosh.__doc__ = parser_bosh().format_help()
