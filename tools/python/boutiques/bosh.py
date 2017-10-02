#!/usr/bin/env python

from argparse import ArgumentParser, RawTextHelpFormatter
import os, sys

class BoutiquesEndpoints():
    def bosh_validate(self, params):
        parser = ArgumentParser("Boutiques descriptor validator")
        parser.add_argument("descriptor", action="store",
                            help="The Boutiques descriptor.")
        parser.add_argument("--bids", "-b", action="store_true",
                            help="Flag indicating if descriptor is a BIDS app")
        results = parser.parse_args(params)

        from boutiques.validator import validate_descriptor
        descriptor = validate_descriptor(results.descriptor)

        if results.bids:
            from boutiques.bids import validate_bids
            validate_bids(descriptor, valid=True)

        # If it gets here without error, return code 0
        return 0
    
    def bosh_execute(self, params):
        parser = ArgumentParser("Boutiques local executor", add_help=False)
        parser.add_argument("mode", action="store",
                            help="Mode of operation to use. Launch: takes a "
                            "set of inputs compliant with invocation schema "
                            "and launches the tool. Simulate: shows sample "
                            "command-lines based on the provided descriptor"
                            " based on provided or randomly generated "
                            "inputs.", choices=["launch", "simulate"])
        parser.add_argument("descriptor", action="store",
                            help="The Boutiques descriptor.")
        parser.add_argument("--help", "-h", action="store_true",
                            help="show this help message and exit")

        args, params = parser.parse_known_args(params)
        descriptor = args.descriptor
        mode = args.mode
        params += ["--help"] if args.help is True else []

        def errExit(msg, print_usage = True):
          if print_usage: parser.print_usage()
          sys.stderr.write("Error: " + msg + "\n")
          sys.exit(1)


        if mode == "launch":
            parser = ArgumentParser("Launches an invocation.")
            parser.add_argument("input", action="store",
                                help="Input JSON complying to invocation.")
            parser.add_argument("-v", "--volumes", action="store", type=str,
                                help="Volumes to mount when launching the "
                                "container. Format consistently the following:"
                                " /a:/b will mount local direcotry /a to "
                                "container directory /b.", nargs="*")
            parser.add_argument("-x", "--debug", action="store_true",
                                help="Keeps temporary scripts used during "
                                "execution.")
            results = parser.parse_args(params)

            # Do some basic input scrubbing
            inp = results.input
            if not os.path.isfile(inp):
                errExit("Input file {} does not exist.".format(inp), False)
            elif not inp.endswith(".json"):
                errExit("Input file {} must end in 'json'.".format(inp), False)
            elif not os.path.isfile(descriptor):
                errExit("JSON descriptor {} does not seem to exist.".format(descriptor), False)

            # Generate object that will perform the commands
            from boutiques.localExec import LocalExecutor
            executor = LocalExecutor(descriptor,
                                     {"forcePathType"      : True,
                                      "destroyTempScripts" : not results.debug,
                                      "changeUser"         : True})
            executor.readInput(inp)
            # Execute it
            exit_code = executor.execute(results.volumes)
            if exit_code:
                sys.exit(exit_code)

        elif mode == "simulate":
            parser = ArgumentParser("Simulates an invocation.")
            parser.add_argument("-i", "--input", action="store",
                                help="Input JSON complying to invocation.")
            parser.add_argument("-r", "--random", action="store_true",
                                help="Generate random set of inputs.")
            parser.add_argument("-n", "--number", type=int, action="store",
                                help="Number of random input sets to create.")
            results = parser.parse_args(params)

            # Do some basic input scrubbing
            inp = results.input
            rand = results.random
            numb = results.number
            if numb and numb < 1:
                errExit("--number value must be positive.", False)
            elif numb and not rand:
                errExit("--number value requires --random setting.")
            elif rand and inp:
              errExit("--random setting and --input value cannot be used together.")
            elif inp and not os.path.isfile(inp):
                errExit("Input file {} does not exist.".format(inp), False)
            elif inp and not inp.endswith(".json"):
                errExit("Input file {} must end in 'json'.".format(inp), False)
            elif not os.path.isfile(descriptor):
                errExit("JSON descriptor {} does not seem to exist.".format(descriptor), False)
            elif not rand and not inp:
              errExit("The default mode requires an input (-i).")
            elif not numb:
              numb = 1

            # Generate object that will perform the commands
            from boutiques.localExec import LocalExecutor
            executor = LocalExecutor(descriptor,
                                     {"forcePathType"      : True,
                                      "destroyTempScripts" : True,
                                      "changeUser"         : True})
            if rand:
                executor.generateRandomParams(numb)
                executor.printCmdLine()
            else:
                executor.readInput(inp)
                executor.printCmdLine()

        else:
            parser.print_help()
    
    def bosh_import(self, params):
        parser = ArgumentParser(description="Publish a clowdr analysis.")
        parser.add_argument("analysis", action="store", help="JSON object for "
                            "an analysis in the clowdr schema.")
        parser.add_argument("--no-cache", "-n", action="store_true",
                            help="Ignores local copies of fetched files.")
        parser.add_argument("--local", "-l", action="store_true",
                            help="Launches the service on your machine.")
        inp = parser.parse_args(params)
        print(inp)
        print("TODO: All this function")
    
    def bosh_publish(self, params):
        print(params)
        parser = ArgumentParser(description="Validator for a clowdr analysis.")
        parser.add_argument("analysis", action="store", help="JSON object for "
                            "an analysis in the clowdr schema.")
        parser.add_argument("--no-cache", "-n", action="store_true",
                            help="Ignores local copies of fetched files.")
        parser.add_argument("--offline", "-o", action="store_true",
                            help="Doesn't attempt to fetch remote files.")
        inp = parser.parse_args(params)
        print(inp)
        print("TODO: All this function")
    
    def bosh_invocation(self, params):
        parser = ArgumentParser(description="Generator for a clowdr analysis.")
        parser.add_argument("analysis", action="store", help="JSON object to "
                            "store the generated analysis object.")
        inp = parser.parse_args(params)
        print(inp)
        print("TODO: All this function")


def bosh(args=None):
    parser = ArgumentParser(description="Driver for Bosh functions",
                            add_help=False)
    parser.add_argument("function", action="store", nargs="?",
                        help="The tool within boutiques/bosh you wish to run. "
                        "Validate: validates an existing boutiques descriptor."
                        "Exec: launches or simulates an execution given a "
                        "descriptor and a set of inputs. Import: creates a "
                        "descriptor for a BIDS app or updates a descriptor "
                        "from an older version of the schema. Publish: creates"
                        "an entry in NeuroLinks for the descriptor and tool."
                        "Invocation: generates the invocation schema for a "
                        "given descriptor.",
                        choices=["validate", "exec", "import",
                                 "publish", "invocation"])
    parser.add_argument("--help", "-h", action="store_true",
                        help="show this help message and exit")

    args, params = parser.parse_known_args(args)
    func = args.function
    params += ["--help"] if args.help is True else []

    endpoints = BoutiquesEndpoints()
    if func == "validate":
        out = endpoints.bosh_validate(params)
        return out
    elif func == "exec":
        out = endpoints.bosh_execute(params)
        return out
    elif func == "import":
        out = endpoints.bosh_import(params)
        return out
    elif func == "publish":
        out = endpoints.bosh_publish(params)
        return out
    elif func == "invocation":
        out = endpoints.bosh_invocation(params)
        return out
    else:
        parser.print_help()
