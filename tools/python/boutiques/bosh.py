#!/usr/bin/env python

import jsonschema
import json
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
from boutiques.localExec import loadJson
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
        parser.add_argument("-v", "--volumes", action="store", type=str,
                            help="Volumes to mount when launching the "
                            "container. Format consistently the following:"
                            " /a:/b will mount local directory /a to "
                            "container directory /b.", nargs="*")
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
                            help="Location of Singularity image "
                            "(default is current directory).")
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
                                  "imagePath": results.imagepath})
        # Execute it
        return executor.execute(results.volumes)

    if mode == "simulate":
        parser = ArgumentParser("Simulates an invocation.")
        parser.add_argument("descriptor", action="store",
                            help="The Boutiques descriptor as a JSON file, "
                            "JSON string or Zenodo ID (prefixed by 'zenodo.').")
        parser.add_argument("-i", "--input", action="store",
                            help="Input JSON complying to invocation.")
        parser.add_argument("-r", "--random", action="store", type=int,
                            nargs="*", help="Generate random set of inputs.")
        results = parser.parse_args(params)
        descriptor = results.descriptor

        # Do some basic input scrubbing
        inp = results.input
        rand = results.random is not None
        numb = results.random[0] if rand and len(results.random) > 0 else 1

        if numb and numb < 1:
            raise_error(SystemExit, "--number value must be positive.")
            # raise SystemExit("--number value must be positive.")
        if rand and inp:
            raise_error(SystemExit, "--random setting and --input value cannot "
                        "be used together.")
        if inp and not os.path.isfile(inp):
            raise_error(SystemExit, "Input file {} does not exist.".format(inp))
        if inp and not inp.endswith(".json"):
            raise_error(SystemExit, "Input file {} must end in 'json'.".
                        format(inp))
        if not rand and not inp:
            raise_error(SystemExit, "The default mode requires an input (-i).")

        valid = invocation(descriptor, '-i', inp) if inp else\
            invocation(descriptor)

        # Generate object that will perform the commands
        from boutiques.localExec import LocalExecutor
        executor = LocalExecutor(descriptor, inp,
                                 {"forcePathType": True,
                                  "destroyTempScripts": True,
                                  "changeUser": True})
        if rand:
            executor.generateRandomParams(numb)
        executor.printCmdLine()

        # for consistency with execute
        # Adding hide to "container location" field since it's an invalid
        # value, and we can parse that to hide the summary print
        return ExecutorOutput(os.linesep.join(executor.cmd_line), "",
                              0, "", [], [], "", "", "hide")

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
                            help="Location of Singularity image "
                            "(default is current directory).")
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
                                  "imagePath": results.imagepath})
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

    results = parser.parse_args(params)

    from boutiques.publisher import Publisher
    publisher = Publisher(results.boutiques_descriptor,
                          results.verbose,
                          results.sandbox,
                          results.no_int,
                          results.zenodo_token)
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
    if result.invocation:
        data = loadJson(result.invocation)
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
                              "changeUser": True})

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
        # Create temporary file for the invocation() function.
        invocation_JSON = test["invocation"]
        temp_invocation_JSON = tempfile.NamedTemporaryFile(suffix=".json",
                                                           delete=False)
        temp_invocation_JSON.write(json.dumps(invocation_JSON).encode())
        temp_invocation_JSON.seek(0)
        # Check if the invocation is valid.
        invocation(result.descriptor, "--invocation", temp_invocation_JSON.name)
        # Destroy the temporary file.
        temp_invocation_JSON.close()

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
    parser.add_argument("-m", "--max", action="store",
                        help="Specify the maximum number of results "
                        "to be returned. Default is 10.")

    result = parser.parse_args(params)

    from boutiques.searcher import Searcher
    searcher = Searcher(result.query, result.verbose, result.sandbox,
                        result.max)

    return searcher.search()


def pull(*params):
    parser = ArgumentParser("Download a descriptor from Zenodo.")

    parser.add_argument("zid", action="store", help="Zenodo ID "
                        "of the descriptor to pull, prefixed by "
                        "'zenodo.', e.g. zenodo.123456")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print information messages")
    parser.add_argument("--sandbox", action="store_true",
                        help="pull from Zenodo's sandbox instead of "
                        "production server. Recommended for tests.")

    result = parser.parse_args(params)

    from boutiques.puller import Puller
    puller = Puller(result.zid, result.verbose, True, result.sandbox)

    return puller.pull()


def bosh(args=None):
    parser = ArgumentParser(description="Driver for Bosh functions",
                            add_help=False)
    parser.add_argument("function", action="store", nargs="?",
                        help="The tool within boutiques/bosh you wish to run. "
                        "Create: creates an Boutiques descriptor from scratch. "
                        "Validate: validates an existing boutiques descriptor. "
                        "Exec: launches or simulates an execution given a "
                        "descriptor and a set of inputs. Import: creates a "
                        "descriptor for a BIDS app or updates a descriptor "
                        "from an older version of the schema. Export: exports a"
                        "descriptor to other formats. Publish: creates"
                        "an entry in Zenodo for the descriptor and "
                        "adds the DOI created by Zenodo to the descriptor. "
                        "Invocation: generates the invocation schema for a "
                        "given descriptor. Eval: given an invocation and a "
                        "descriptor, queries execution properties. "
                        "Test: run pytest on a descriptor detailing tests. "
                        "Search: search Zenodo for descriptors. "
                        "Pull: download a descriptor from Zenodo. "
                        "Pprint: generate pretty help text from a descriptor.",
                        choices=["create", "validate", "exec", "import",
                                 "export", "publish", "invocation", "evaluate",
                                 "test", "search", "pull", "pprint"])

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
