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
        neurolinks_github_repo_url = "https://github.com/brainhack101/neurolinks"
        neurolinks_dest_path = os.path.join(os.getenv("HOME"),"neurolinks")
        
        def get_neurolinks_default():
            if os.path.isdir(neurolinks_dest_path):
                return neurolinks_dest_path
            return neurolinks_github_repo_url
        
        parser = ArgumentParser("Boutiques publisher",
                                description="A publisher of Boutiques tools in Neurolinks"
                                "(https://brainhack101.github.io/neurolinks). Crawls a Git"
                                "repository for valid Boutiques descriptors and imports them"
                                "in Neurolinks format. Uses your GitHub account to fork the "
                                "Neurolinks repository and commit new tools in it. Requires "
                                "that your GitHub ssh key is configured and usable without"
                                "password.")
        parser.add_argument("boutiques_repo", action="store",
                            help="Local path to a Git repository containing Boutiques "
                            "descriptors to publish.")
        parser.add_argument("author_name", action="store",
                            help="Default author name.")
        parser.add_argument("tool_url", action="store",
                            help="Default tool URL.")
        parser.add_argument("--neurolinks-repo", "-n", action="store",
                            default=get_neurolinks_default(),
                            help="Local path to a Git clone of {0}. Remotes: 'origin' "
                            "should point to a writable fork from which a PR will be "
                            "initiated; 'base' will be pulled before any update, should "
                            "point to {0}. If a URL is provided, will attempt to fork it on"
                            " GitHub and clone it to {1}.".format(neurolinks_github_repo_url,
                                                                  neurolinks_dest_path))
        parser.add_argument("--boutiques-remote", "-r", action="store",
                            default='origin',
                            help="Name of Boutiques Git repo remote used to get URLs of"
                            " Boutiques descriptor.")
        parser.add_argument("--no-github", action="store_true",
                            help="Do not interact with GitHub at all (useful for tests).")
        parser.add_argument("--github-login", "-u", action="store",
                            help="GitHub login used to fork, clone and PR to {}. Defaults to"
                            " value in $HOME/.pygithub. Saved in $HOME/.pygithub if "
                            "specified.".format(neurolinks_github_repo_url))
        parser.add_argument("--github-password", "-p", action="store",
                            help="GitHub password used to fork, clone and PR to {}. Defaults"
                            " to value in $HOME/.pygithub. Saved in $HOME/.pygithub if "
                            "specified.".format(neurolinks_github_repo_url))
        parser.add_argument("--inter", "-i", action="store_true",
                            default = False,
                            help="Interactive mode. Does not use default values everywhere, "
                            "checks if URLs are correct or accessible.")

        results = parser.parse_args(params)

        from boutiques.publisher import Publisher
        publisher = Publisher(results.boutiques_repo, results.boutiques_remote,
                              results.author_name, results.tool_url, results.inter,
                              results.neurolinks_repo, neurolinks_dest_path,
                              results.github_login, results.github_password, results.no_github).publish()
    
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
