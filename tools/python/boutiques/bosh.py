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
from boutiques.invocationSchemaHandler import InvocationValidationError
from boutiques.localExec import ExecutorOutput
from boutiques.localExec import ExecutorError
from boutiques.exporter import ExportError
from boutiques.importer import ImportError
from boutiques.localExec import addDefaultValues
from boutiques.util.utils import loadJson
from boutiques.logger import raise_error
from tabulate import tabulate


def prettyprint(*params):
    parser = ArgumentParser("Boutiques pretty-print for generating help text")
    parser.add_argument("descriptor", action="store",
                        help="The Boutiques descriptor.")
    results = parser.parse_args(params)

    from boutiques.prettyprint import PrettyPrinter
    desc = loadJson(results.descriptor)
    prettyclass = PrettyPrinter(desc)

    return prettyclass.docstring


def create(*params):
    parser = ArgumentParser("Boutiques descriptor creator")
    parser.add_argument("descriptor", action="store",
                        help="Output file to store descriptor in.")
    parser.add_argument("--docker-image", '-d', action="store",
                        help="Name of Docker image on DockerHub.")
    parser.add_argument("--use-singularity", '-u', action="store_true",
                        help="When --docker-image is used. Specify to "
                             "use singularity to run it.")
    results = parser.parse_args(params)

    from boutiques.creator import CreateDescriptor
    new = CreateDescriptor(parser=None,
                           docker_image=results.docker_image,
                           use_singularity=results.use_singularity)
    new.save(results.descriptor)
    return None


def validate(*params):
    parser = ArgumentParser("Boutiques descriptor validator")
    parser.add_argument("descriptor", action="store",
                        help="The Boutiques descriptor as a JSON file, JSON "
                             "string or Zenodo ID (prefixed by 'zenodo.').")
    parser.add_argument("--bids", "-b", action="store_true",
                        help="Flag indicating if descriptor is a BIDS app")
    parser.add_argument("--format", "-f", action="store_true",
                        help="If descriptor is valid, rewrite it with sorted"
                        " keys.")
    results = parser.parse_args(params)

    from boutiques.validator import validate_descriptor
    descriptor = validate_descriptor(results.descriptor,
                                     format_output=results.format)
    if results.bids:
        from boutiques.bids import validate_bids
        validate_bids(descriptor, valid=True)


def execute(*params):
    parser = ArgumentParser("Boutiques local executor", add_help=False)
    parser.add_argument("mode", action="store",
                        help="Mode of operation to use. Launch: takes a "
                        "set of inputs compliant with invocation schema "
                        "and launches the tool. Simulate: shows sample "
                        "command-lines based on the provided descriptor"
                        " based on provided or randomly generated inputs. "
                        "Prepare: pulls the Docker or Singularity container "
                        "image for a given descriptor. ",
                        choices=["launch", "simulate", "prepare"])
    parser.add_argument("--help", "-h", action="store_true",
                        help="show this help message and exit")

    helps = any([True for ht in ["--help", "-h"] if ht in params])
    if len(params) <= 1 and helps:
        parser.print_help()
        raise SystemExit

    args, params = parser.parse_known_args(params)
    mode = args.mode
    params += ["--help"] if args.help is True else []

    if mode == "launch":
        parser = ArgumentParser("Launches an invocation.")
        parser.add_argument("descriptor", action="store",
                            help="The Boutiques descriptor as a JSON file, "
                            "JSON string or Zenodo ID (prefixed by 'zenodo.').")
        parser.add_argument("invocation", action="store",
                            help="Input JSON complying to invocation.")
        parser.add_argument("-v", "--volumes", action="append", type=str,
                            help="Volumes to mount when launching the "
                            "container. Format consistently the following:"
                            " /a:/b will mount local directory /a to "
                            "container directory /b.")
        parser.add_argument("-x", "--debug", action="store_true",
                            help="Keeps temporary scripts used during "
                            "execution, and prints additional debug "
                            "messages.")
        parser.add_argument("-u", "--user", action="store_true",
                            help="Runs the container as local user ({0})"
                            " instead of root.".format(os.getenv("USER")))
        parser.add_argument("-s", "--stream", action="store_true",
                            help="Streams stdout and stderr in real time "
                            "during execution.")
        parser.add_argument("--imagepath", action="store",
                            help="Path to Singularity image. "
                            "If not specified, will use current directory.")
        parser.add_argument("--skip-data-collection", action="store_true",
                            help="Skips execution data collection and saving"
                            "to cache.")
        force_group = parser.add_mutually_exclusive_group()
        force_group.add_argument("--force-docker", action="store_true",
                                 help="Tries to run Singularity images with "
                                 "Docker. This only works if the image is on"
                                 "Docker Hub, i.e. has index docker://")
        force_group.add_argument("--force-singularity", action="store_true",
                                 help="Tries to run Docker images with "
                                 "Singularity.")
        results = parser.parse_args(params)
        descriptor = results.descriptor
        inp = results.invocation

        # Validate invocation and descriptor
        valid = invocation(descriptor, '-i', inp)

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
                                      results.force_singularity})
        # Execute it
        return executor.execute(results.volumes)

    if mode == "simulate":
        parser = ArgumentParser("Simulates an invocation.")
        parser.add_argument("descriptor", action="store",
                            help="The Boutiques descriptor as a JSON file, "
                            "JSON string or Zenodo ID (prefixed by 'zenodo.').")
        parser.add_argument("-i", "--input", action="store",
                            help="Input JSON complying to invocation.")
        parser.add_argument("-j", "--json", action="store_true",
                            help="Flag to generate invocation in JSON format.")
        parser.add_argument("-c", "--complete", action="store_true",
                            help="Include optional parameters.")
        results = parser.parse_args(params)

        descriptor = results.descriptor

        # Do some basic input scrubbing
        inp = results.input

        arguments = [descriptor]
        if inp:
            arguments.append('-i')
            arguments.append(inp)
        valid = invocation(*arguments)

        # Generate object that will perform the commands
        from boutiques.localExec import LocalExecutor
        executor = LocalExecutor(descriptor, inp,
                                 {"forcePathType": True,
                                  "destroyTempScripts": True,
                                  "changeUser": True,
                                  "skipDataCollect": True,
                                  "requireComplete": results.complete})
        if not inp:
            executor.generateRandomParams(1)

        if results.json:
            sout = [json.dumps(executor.in_dict, indent=4, sort_keys=True)]
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
        parser = ArgumentParser("Pulls the container image for a given "
                                "descriptor")
        parser.add_argument("descriptor", action="store",
                            help="The Boutiques descriptor as a JSON file, "
                            "JSON string or Zenodo ID (prefixed by 'zenodo.').")
        parser.add_argument("-x", "--debug", action="store_true",
                            help="Keeps temporary scripts used during "
                            "execution, and prints additional debug "
                            "messages.")
        parser.add_argument("-s", "--stream", action="store_true",
                            help="Streams stdout and stderr in real time "
                            "during execution.")
        parser.add_argument("--imagepath", action="store",
                            help="Path to Singularity image. "
                            "If not specified, will use current directory.")
        results = parser.parse_args(params)
        descriptor = results.descriptor

        # Validate descriptor
        valid = invocation(descriptor)

        # Generate object that will perform the commands
        from boutiques.localExec import LocalExecutor
        executor = LocalExecutor(descriptor, None,
                                 {"forcePathType": True,
                                  "debug": results.debug,
                                  "stream": results.stream,
                                  "imagePath": results.imagepath,
                                  "skipDataCollect": True})
        container_location = executor.prepare()[1]
        print("Container location: " + container_location)

        # Adding hide to "container location" field since it's an invalid
        # value, and we can parse that to hide the summary print
        return ExecutorOutput(container_location, "",
                              0, "", [], [], "", "", "hide")


def importer(*params):
    parser = ArgumentParser("Imports old descriptor or BIDS app or CWL "
                            " descriptor to spec.")
    parser.add_argument("type", help="Type of import we are performing",
                        choices=["bids", "0.4", "cwl"])
    parser.add_argument("output_descriptor", help="Where the Boutiques"
                        " descriptor will be written.")
    parser.add_argument("input_descriptor", help="Input descriptor to be "
                        "converted. For '0.4'"
                        ", is JSON descriptor,"
                        " for 'bids' is base directory of BIDS app, "
                        "for 'cwl' is YAML descriptor.")
    parser.add_argument("-o", "--output-invocation", help="Where to write "
                        "the invocation if any.")
    parser.add_argument("-i", "--input-invocation", help="Input invocation "
                        " for CWL if any.")
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


def exporter(*params):
    parser = ArgumentParser("Export Boutiques descriptor to other formats.")
    parser.add_argument("type", help="Type of export we are performing.",
                        choices=["carmin"])
    parser.add_argument("descriptor", help="Boutiques descriptor to export.")
    parser.add_argument("--identifier", help="Identifier to use in"
                                             "CARMIN export.")
    parser.add_argument("output", help="Output file where to write the"
                        " converted descriptor.")
    results = parser.parse_args(params)

    descriptor = results.descriptor
    output = results.output

    bosh(["validate", results.descriptor])

    from boutiques.exporter import Exporter
    exporter = Exporter(descriptor, results.identifier)
    if results.type == "carmin":
        exporter.carmin(output)


def publish(*params):
    parser = ArgumentParser("Boutiques publisher",
                            description="A publisher of Boutiques tools"
                            " in Zenodo (http://zenodo.org). Requires "
                            "a Zenodo access token, see "
                            "http://developers.zenodo.org/#authentication.")
    parser.add_argument("boutiques_descriptor", action="store",
                        help="local path of the "
                        " Boutiques descriptor to publish.")
    parser.add_argument("--sandbox", action="store_true",
                        help="publish to Zenodo's sandbox instead of "
                        "production server. Recommended for tests.")
    parser.add_argument("--zenodo-token", action="store",
                        help="Zenodo API token to use for authentication. "
                        "If not used, token will be read from configuration "
                        "file or requested interactively.")
    parser.add_argument("--no-int", '-y', action="store_true",
                        help="disable interactive input.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print information messages.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--replace", action="store_true",
                       help="Publish an updated version of an existing "
                       "record. The descriptor must contain a DOI, which "
                       "will be replaced with a new one.")
    group.add_argument("--id", action="store",
                       help="Zenodo ID of an existing record you wish to "
                       "update with a new version, prefixed by "
                       "'zenodo.' (e.g. zenodo.123456).")

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
    parser = ArgumentParser("Creates invocation schema and validates"
                            " invocations. Uses descriptor's invocation"
                            " schema if it exists, otherwise creates one.")
    parser.add_argument("descriptor", action="store",
                        help="The Boutiques descriptor as a JSON file, JSON "
                             "string or Zenodo ID (prefixed by 'zenodo.').")
    parser.add_argument("-i", "--invocation", action="store",
                        help="Input values in a JSON file or as a JSON "
                        "object to be validated against "
                        "the invocation schema.")
    parser.add_argument("-w", "--write-schema", action="store_true",
                        help="If descriptor doesn't have an invocation "
                        "schema, creates one and writes it to the descriptor"
                        " file ")
    result = parser.parse_args(params)
    validate(result.descriptor)
    descriptor = loadJson(result.descriptor)
    if descriptor.get("invocation-schema"):
        invSchema = descriptor.get("invocation-schema")
    else:
        from boutiques.invocationSchemaHandler import generateInvocationSchema
        invSchema = generateInvocationSchema(descriptor)
        if result.write_schema:
            descriptor["invocation-schema"] = invSchema
            with open(result.descriptor, "w") as f:
                f.write(json.dumps(descriptor, indent=4, sort_keys=True))
    if result.invocation:
        from boutiques.invocationSchemaHandler import validateSchema
        data = addDefaultValues(descriptor, loadJson(result.invocation))
        validateSchema(invSchema, data)


def evaluate(*params):
    parser = ArgumentParser("Evaluates parameter values for a descriptor"
                            " and invocation")
    parser.add_argument("descriptor", action="store",
                        help="The Boutiques descriptor as a JSON file, JSON "
                             "string or Zenodo ID (prefixed by 'zenodo.').")
    parser.add_argument("invocation", action="store",
                        help="Input JSON complying to invocation.")
    parser.add_argument("query", action="store", nargs="*",
                        help="The query to be performed. Simply request keys "
                        "from the descriptor (i.e. output-files), and chain "
                        "together queries (i.e. id=myfile or optional=false) "
                        "slashes between them and commas connecting them. "
                        "(i.e. output-files/optional=false,id=myfile). "
                        "Perform multiple queries by separating them with a "
                        "space.")
    result = parser.parse_args(params)

    # Generate object that will parse the invocation and descriptor
    from boutiques.localExec import LocalExecutor
    executor = LocalExecutor(result.descriptor, result.invocation,
                             {"forcePathType": True,
                              "destroyTempScripts": True,
                              "changeUser": True,
                              "skipDataCollect": True})

    from boutiques.evaluate import evaluateEngine
    query_results = []
    for query in result.query:
        query_results += [evaluateEngine(executor, query)]
    return query_results[0] if len(query_results) == 1 else query_results


def test(*params):

    parser = ArgumentParser("Perform all the tests defined within the"
                            " given descriptor")
    parser.add_argument("descriptor", action="store",
                        help="The Boutiques descriptor as a JSON file, JSON "
                             "string or Zenodo ID (prefixed by 'zenodo.').")
    result = parser.parse_args(params)

    # Generation of the invocation schema (and descriptor validation).
    invocation(result.descriptor)

    # Extraction of all the invocations defined for the test-cases.
    descriptor = loadJson(result.descriptor)

    if (not descriptor.get("tests")):
        # If no tests have been specified, we consider testing successful.
        return 0

    for test in descriptor["tests"]:
        invocation_JSON = test["invocation"]

        # Check if the invocation is valid.
        invocation(result.descriptor, "--invocation",
                   json.dumps(invocation_JSON))

    # Invocations have been properly validated. We can launch the actual tests.
    test_path = op.join(op.dirname(op.realpath(__file__)), "test.py")
    return pytest.main([test_path, "--descriptor", result.descriptor])


def search(*params):
    parser = ArgumentParser("Search Zenodo for Boutiques descriptors. "
                            "When no term is supplied, will search for "
                            "all descriptors.")
    parser.add_argument("query", nargs="?", default="boutiques",
                        action="store", help="Search query")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print information messages")
    parser.add_argument("--sandbox", action="store_true",
                        help="search Zenodo's sandbox instead of "
                        "production server. Recommended for tests.")
    parser.add_argument("-m", "--max", action="store", type=int,
                        help="Specify the maximum number of results "
                        "to be returned. Default is 10.")
    parser.add_argument("-nt", "--no-trunc", action="store_true",
                        help="Do not truncate long tool descriptions.")
    parser.add_argument("-e", "--exact", action="store_true",
                        help="Only return results containing the exact query.")

    result = parser.parse_args(params)

    from boutiques.searcher import Searcher
    searcher = Searcher(result.query, result.verbose, result.sandbox,
                        result.max, result.no_trunc, result.exact)

    return searcher.search()


def example(*params):
    parser = ArgumentParser("Generates example invocation from a valid"
                            "descriptor")
    parser.add_argument("descriptor", action="store",
                        help="The Boutiques descriptor as a JSON file, "
                        "JSON string or Zenodo ID (prefixed by 'zenodo.').")
    parser.add_argument("-c", "--complete", action="store_true",
                        help="Include optional parameters.")
    results = parser.parse_args(params)

    descriptor = results.descriptor
    valid = invocation(descriptor)

    # Generate object that will perform the commands
    from boutiques.localExec import LocalExecutor
    executor = LocalExecutor(descriptor, None,
                             {"forcePathType": True,
                              "destroyTempScripts": True,
                              "changeUser": True,
                              "skipDataCollect": True,
                              "requireComplete": results.complete})
    executor.generateRandomParams(1)

    return json.dumps(executor.in_dict, indent=4, sort_keys=True)


def pull(*params):
    parser = ArgumentParser("Ensures that Zenodo descriptors are locally "
                            "cached, downloading them if needed.")

    parser.add_argument("zids", nargs="+", action="store", help="One or "
                        "more Zenodo IDs for the descriptor(s) to pull, "
                        "prefixed by 'zenodo.', e.g. zenodo.123456 "
                        "zenodo.123457")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print information messages")
    parser.add_argument("--sandbox", action="store_true",
                        help="pull from Zenodo's sandbox instead of "
                        "production server. Recommended for tests.")

    result = parser.parse_args(params)

    from boutiques.puller import Puller
    puller = Puller(result.zids, result.verbose, result.sandbox)
    return puller.pull()


def data(*params):
    parser = ArgumentParser("Manage execution data collection.", add_help=False)

    parser.add_argument("action", action="store",
                        help="Manage execution data records. Inspect: displays "
                        "the unpublished records currently in the cache. "
                        "Publish: publishes contents of cache to Zenodo as "
                        "a public data set. Requires a Zenodo access token, "
                        "see http://developers.zenodo.org/#authentication. "
                        "Delete: remove one or more records from the cache.",
                        choices=["inspect", "publish", "delete"])
    parser.add_argument("--help", "-h", action="store_true",
                        help="show this help message and exit")

    helps = any([True for ht in ["--help", "-h"] if ht in params])
    if len(params) <= 1 and helps:
        parser.print_help()
        raise SystemExit

    args, params = parser.parse_known_args(params)
    action = args.action
    params += ["--help"] if args.help is True else []

    if action == "inspect":
        parser = ArgumentParser("Displays contents of cache")
        parser.add_argument("-e", "--example", action="store_true",
                            help="Display example data file contents.")
        results = parser.parse_args(params)

        from boutiques.dataHandler import DataHandler
        dataHandler = DataHandler()
        return dataHandler.inspect(results.example)

    if action == "publish":
        parser = ArgumentParser("Publishes record(s) to a Zenodo data set.")
        parser.add_argument("-a", "--author", action="store",
                            help="Set the author name for the data set "
                            "publication. Defaults to anonymous.")
        parser.add_argument("-f", "--file", action="store",
                            help="Filename of record to publish alone as a "
                            "data set.")
        parser.add_argument("-i", "--individually", action="store_true",
                            help="Publishes all data files in cache as "
                            "independent data sets, By Default will publish "
                            "files in bulk data sets.")
        parser.add_argument("--no-int", '-y', action="store_true",
                            help="disable interactive input.")
        parser.add_argument("-v", "--verbose", action="store_true",
                            help="print information messages.")
        parser.add_argument("--sandbox", action="store_true",
                            help="publish to Zenodo's sandbox instead of "
                            "production server. Recommended for tests.")
        parser.add_argument("--zenodo-token", action="store",
                            help="Zenodo API token to use for authentication. "
                            "If not used, token will be read from "
                            "configuration file or requested interactively.")
        results = parser.parse_args(params)

        from boutiques.dataHandler import DataHandler
        dataHandler = DataHandler()
        return dataHandler.publish(results.file, results.zenodo_token,
                                   results.author, results.individually,
                                   results.sandbox, results.no_int,
                                   results.verbose)

    if action == "delete":
        parser = ArgumentParser("Delete data record(s) in cache.")
        parser.add_argument("-f", "--file", action="store",
                            help="Filename of record to delete.")
        parser.add_argument("--no-int", '-y', action="store_true",
                            help="disable interactive input.")
        results = parser.parse_args(params)

        from boutiques.dataHandler import DataHandler
        dataHandler = DataHandler()
        return dataHandler.delete(results.file, results.no_int)


def bosh(args=None):
    parser = ArgumentParser(add_help=False,
                            formatter_class=RawTextHelpFormatter)
    helptext = r'''
               BOUTIQUES COMMANDS

TOOL CREATION
* create: create a Boutiques descriptor from scratch.
* export: export a descriptor to other formats.
* import: create a descriptor for a BIDS app or update a descriptor from \
    an older version of the schema.
* validate: validate an existing boutiques descriptor.

TOOL USAGE & EXECUTION
* example: generate example command-line for descriptor.
* pprint: generate pretty help text from a descriptor.
* exec: launch or simulate an execution given a descriptor and a set of inputs.
* test: run pytest on a descriptor detailing tests.

TOOL SEARCH & PUBLICATION
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
    parser.add_argument("function", action="store", nargs="?",
                        help=helptext,
                        choices=sorted(
                                ["create", "validate", "exec",
                                 "import", "export", "publish",
                                 "invocation", "evaluate", "test",
                                 "example", "search", "pull",
                                 "data", "pprint", "version"]))

    parser.add_argument("--help", "-h", action="store_true",
                        help="show this help message and exit")

    args, params = parser.parse_known_args(args)
    func = args.function
    params += ["--help"] if args.help is True else []

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
            out = prettyprint(*params)
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
        else:
            parser.print_help()
            raise SystemExit

    except (ZenodoError,
            DescriptorValidationError,
            InvocationValidationError,
            ValidationError,
            ExportError,
            ImportError,
            ExecutorError) as e:
        # We don't want to raise an exception when function is called
        # from CLI.'
        if runs_as_cli():
            try:
                print(e.message)  # Python 2 only
            except Exception as ex:
                print(e)
            return 99  # Note: this conflicts with tool error codes.
        raise e
