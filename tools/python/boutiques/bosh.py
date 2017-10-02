#!/usr/bin/env python

from argparse import ArgumentParser, RawTextHelpFormatter
import os

class BoutiquesEndpoints():
    def bosh_validate(self, params):
        parser = ArgumentParser("Boutiques Validator")
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
        # Parse arguments
        description = "A local Boutiques tool executor and debugger."

        parser = ArgumentParser(description = description)
        parser.add_argument('desc', metavar='descriptor', nargs = 1, help = 'A Boutiques JSON descriptor.')
        parser.add_argument('-i', '--input', help = 'Input parameter values complying to the tool invocation schema.')
        parser.add_argument('-e', '--execute', action = 'store_true', help = 'Execute the program with the given inputs.')
        parser.add_argument('-r', '--random', action = 'store_true', help = 'Generate a random set of input parameters to check.')
        parser.add_argument('-n', '--num', type = int, help = 'Number of random parameter sets to examine.')
        parser.add_argument('-v', '--mounts', type=str, nargs="*", help = "Directories to be mounted in the container in addition to $PWD. Will be passed to Docker with -v or to Singularity with -B. Must comply to the syntax accepted by Docker or Singularity. For instance, /a:/b:ro would mount host directory /a to container directory /b with read-only permissions.")
        parser.add_argument('--dontForcePathType', action = 'store_true', help = 'Fail if an input does not conform to absolute-path specification (rather than converting the path type).')
        parser.add_argument('--changeUser', action = 'store_true', help = 'Changes user in a container to the current user (prevents files generated from being owned by root).')
        parser.add_argument('-k', '--keepTempScripts', action = 'store_true', help = 'Do not remove temporary scripts used to execute commands in containers.')
        results = parser.parse_args(params)

        # Check arguments
        desc = results.desc[0]
        def errExit(msg, print_usage = True):
          if print_usage: parser.print_usage()
          sys.stderr.write('Error: ' + msg + '\n')
          sys.exit(1)

        if results.num and results.num < 1:
          errExit('--num was not given an appropriate value')
        elif results.num and not results.random:
          errExit('--num requires random')
        elif results.random and results.execute:
          errExit('--random and --exec cannot be used together')
        elif results.random and results.input:
          errExit('--random and --input cannot be used together')
        elif results.input and not os.path.isfile(results.input):
          errExit('The input file ' + str(results.input) + ' does not seem to exist', False)
        elif results.input and not results.input.endswith(".json") :
          errExit('Input file ' + str(results.input) + ' must end in .json')
        elif results.execute and not results.input:
          errExit('--exec requires --input')
        elif not os.path.isfile(desc):
          errExit('The input JSON descriptor ({0}) does not seem to exist'.format(desc), False)
        elif not results.random and not results.input:
          errExit('The default mode requires an input (-i)')
        elif not results.num:
          results.num = 1

        # Prepare inputs
        inData = results.input
        # Generate object that will perform the commands
        from boutiques.localExec import LocalExecutor
        executor = LocalExecutor(desc, { 'forcePathType'      : not results.dontForcePathType,
                                         'destroyTempScripts' : not results.keepTempScripts,
                                         'changeUser'         : results.changeUser              })

        ### Run the executor with the given parameters ###
        # Execution case
        if results.execute:
          # Read in given input
          executor.readInput(inData)
          # Execute it
          exit_code = executor.execute(results.mounts)
          if exit_code:
            sys.exit(exit_code)
        # Print random case
        elif results.random:
          # Generate random input
          executor.generateRandomParams(results.num)
          # Print the resulting command line
          executor.printCmdLine()
        # Print input case (default: no execution)
        else:
          # Read in given input
          executor.readInput(inData)
          # Print the resulting command line
          executor.printCmdLine()
    
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
    params += [args.help] if args.help is True else []

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


if __name__ == "__main__":
    bosh()
