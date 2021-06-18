#!/usr/bin/env python

import simplejson as json
import os
import sys
import os.path as op
from jsonschema import ValidationError
from boutiques.boshParsers import *
from boutiques.dataHandler import DataHandlerError
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
from boutiques.util.utils import formatSphinxUsage, importCatcher
from boutiques.logger import raise_error, print_error, print_info
from tabulate import tabulate
import argparse


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
                           camel_case=results.camel_case,
                           cl_template=results.cl_template)
    new.save(results.descriptor)
    return None


def validate(*params):
    parser = parser_bosh()
    params = ('validate',) + params
    results = parser.parse_args(params)

    from boutiques.validator import validate_descriptor
    descriptor = loadJson(results.descriptor, sandbox=results.sandbox)
    descriptor = validate_descriptor(descriptor,
                                     descriptor_path=results.descriptor,
                                     format_output=results.format,
                                     sandbox=results.sandbox)
    if results.bids:
        from boutiques.bids import validate_bids
        validate_bids(descriptor, valid=True)


def execute(*params):
    parser = parser_bosh()
    params = ('exec',) + params
    try:
        # Try to parse input with argparse
        results, _ = parser.parse_known_args(params)
    except SystemExit as e:
        print_info(execute.__doc__)
        raise_error(ExecutorError, "Incorrect usage of 'bosh exec'")

    # Validate mode is in params
    if not hasattr(results, 'mode'):
        parser.parse_known_args(params + ('--help',))
        raise_error(ExecutorError,
                    "Missing exec mode {launch, prepare, simulate}.")

    elif results.mode == "launch":
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
                                  "sandbox": results.sandbox,
                                  "noAutomounts": results.no_automounts})
        # Execute it
        return executor.execute(results.volumes)

    elif results.mode == "simulate":
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

    elif results.mode == "prepare":
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
        importer.import_docopt()
    elif results.type == "config":
        create(results.output_descriptor)
        importer.import_config()


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

@importCatcher()
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
    import pytest
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
    params = ('data',) + params
    try:
        # Try to parse input with argparse
        results, _ = parser.parse_known_args(params)
    except SystemExit as e:
        print_info(data.__doc__)
        raise_error(DataHandlerError, "Incorrect usage of 'bosh data'")

    # Validate mode is in params
    if not hasattr(results, 'mode'):
        parser.parse_known_args(params + ('--help',))
        raise_error(DataHandlerError,
                    "Missing data mode {delete, inspect, publish}.")
    elif results.mode == "inspect":
        from boutiques.dataHandler import DataHandler
        dataHandler = DataHandler()
        return dataHandler.inspect(results.example)
    elif results.mode == "publish":
        from boutiques.dataHandler import DataHandler
        dataHandler = DataHandler()
        return dataHandler.publish(results.file, results.zenodo_token,
                                   results.author, results.nexus_token,
                                   results.nexus_org, results.nexus_project,
                                   results.individually, results.sandbox,
                                   results.no_int, results.verbose,
                                   results.nexus)
    elif results.mode == "delete":
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


def bosh(args=None):
    # Returns True if bosh was called from the CLI
    def runs_as_cli():
        return os.path.basename(sys.argv[0]) == "bosh"

    def bosh_return(val, code=0, hide=False, formatted=None):
        if runs_as_cli():
            if not hide and val is not None:
                print(formatted if formatted is not None else val)
            elif not hide:
                print("OK" if code == 0 else "Failed")
            return code  # everything went well
        return val  # calling function wants this value

    # Params are set depending on where bosh is called from
    if runs_as_cli():
        func = sys.argv[1] if len(sys.argv) >= 2 else None
        params = sys.argv[2:] if func is not None else []
    else:
        func = args[0] if len(args) > 0 else args
        params = args[1:] if func is not None else []

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
            print(parser_bosh().format_help())
            raise_error(ExecutorError,
                        "Incorrect bosh mode \'{}\'".format(func))

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
    except SystemExit as e:
        if runs_as_cli():
            print(e)
            return 99  # Note: this conflicts with tool error codes.
        raise_error(BoutiquesError,
                    "Unable to parse arguments resulting in SystemExit.")


class BoutiquesError(Exception):
    pass


# This section is for documentation generation purposes
bosh.__doc__ = parser_bosh().format_usage().replace("sphinx-build", "bosh")
# retrieve subparsers from parser
subparsers_actions = [a for a in parser_bosh()._actions
                      if isinstance(a, argparse._SubParsersAction)]
for action in subparsers_actions:
    # get all subparsers and assign __doc__ to functions
    for func, subparser in action.choices.items():
        usage_string = formatSphinxUsage(func, subparser.format_usage())
        if func == "create":
            create.__doc__ = usage_string
        elif func == "data":
            data.__doc__ = usage_string
        elif func == "deprecate":
            deprecate.__doc__ = usage_string
        elif func == "evaluate":
            evaluate.__doc__ = usage_string
        elif func == "example":
            example.__doc__ = usage_string
        elif func == "exec":
            execute.__doc__ = usage_string
        elif func == "export":
            exporter.__doc__ = usage_string
        elif func == "import":
            importer.__doc__ = usage_string
        elif func == "invocation":
            invocation.__doc__ = usage_string
        elif func == "pprint":
            pprint.__doc__ = usage_string
        elif func == "publish":
            publish.__doc__ = usage_string
        elif func == "pull":
            pull.__doc__ = usage_string
        elif func == "search":
            search.__doc__ = usage_string
        elif func == "test":
            test.__doc__ = usage_string
        elif func == "validate":
            validate.__doc__ = usage_string
