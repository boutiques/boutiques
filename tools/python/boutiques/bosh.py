#!/usr/bin/env python

from argparse import ArgumentParser, RawTextHelpFormatter
import jsonschema
import json
import os, sys

def validate(*params):
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
    
def execute(*params):
    parser = ArgumentParser("Boutiques local executor", add_help=False)
    parser.add_argument("mode", action="store",
                        help="Mode of operation to use. Launch: takes a "
                        "set of inputs compliant with invocation schema "
                        "and launches the tool. Simulate: shows sample "
                        "command-lines based on the provided descriptor"
                        " based on provided or randomly generated "
                        "inputs.", choices=["launch", "simulate"])
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
                            help="The Boutiques descriptor.")
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
        parser.add_argument("-u", "--user", action="store_true",
                            help="Runs the container as local user ({0}) instead of root.".format(os.getenv("USER")))
        results = parser.parse_args(params)
        descriptor = results.descriptor



        # Do some basic input scrubbing
        inp = results.input
        if not os.path.isfile(inp):
            raise SystemExit("Input file {} does not exist".format(inp))
        if not inp.endswith(".json"):
            raise SystemExit("Input file {} must end in json".format(inp))
        if not os.path.isfile(descriptor):
            raise SystemExit("JSON descriptor {} does not exist".format(descriptor))

        # Generate object that will perform the commands
        from boutiques.localExec import LocalExecutor
        executor = LocalExecutor(descriptor,
                                 {"forcePathType"      : True,
                                  "destroyTempScripts" : not results.debug,
                                  "changeUser"         : results.user})
        executor.readInput(inp)
        # Execute it
        exit_code = executor.execute(results.volumes)
        if exit_code:
            raise SystemExit(exit_code)

    if mode == "simulate":
        parser = ArgumentParser("Simulates an invocation.")
        parser.add_argument("descriptor", action="store",
                            help="The Boutiques descriptor.")
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
            raise SystemExit("--number value must be positive.")
        if rand and inp:
            raise SystemExit("--random setting and --input value cannot be used together.")
        if inp and not os.path.isfile(inp):
            raise SystemExit("Input file {} does not exist.".format(inp))
        if inp and not inp.endswith(".json"):
            raise SystemExit("Input file {} must end in 'json'.".format(inp))
        if not os.path.isfile(descriptor):
            raise SystemExit("JSON descriptor {} does not seem to exist.".format(descriptor))
        if not rand and not inp:
            raise SystemExit("The default mode requires an input (-i).")

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

def importer(*params):
    parser = ArgumentParser("Imports old descriptor or BIDS app to spec.")
    parser.add_argument("type", help="Type of import we are performing",
                        choices=["bids", "0.4"])
    parser.add_argument("descriptor", help="Where the Boutiques descriptor will be written.")
    parser.add_argument("input", help="Input to be convered. For '0.4', is JSON descriptor,"
                        " for 'bids' is base directory of BIDS app.")
    results = parser.parse_args(params)

    descriptor = results.descriptor
    inp = results.input
    from boutiques.importer import Importer
    importer = Importer(descriptor)
    if results.type == "0.4":
        importer.upgrade_04(inp)
    elif results.type == "bids":
        importer.import_bids(inp)

def publish(*params):
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

def invocation(*params):
    parser = ArgumentParser("Creates invocation schema and validates invocations")
    parser.add_argument("descriptor", action="store",
                        help="The Boutiques descriptor.")
    parser.add_argument("-i", "--invocation", action="store",
                        help="Input values in a JSON file to be validated against "
                        "the invocation schema.")
    result = parser.parse_args(params)

    try:
        from boutiques.validator import validate_descriptor
        validate_descriptor(result.descriptor)
        if result.invocation:
            data = json.loads(open(result.invocation).read())
    except Exception as e:
        print("Error reading JSON:")
        raise ValidationError(e.message)

    descriptor = json.loads(open(result.descriptor).read())
    if descriptor.get("invocation-schema"):
        invSchema = descriptor.get("invocation-schema")
    else:
        from boutiques.invocationSchemaHandler import generateInvocationSchema
        invSchema = generateInvocationSchema(descriptor)
        
    descriptor["invocation-schema"] = invSchema
    with open(result.descriptor, "w") as f:
        f.write(json.dumps(descriptor, indent=4, sort_keys=True))
    if result.invocation:
        from boutiques.invocationSchemaHandler import validateSchema
        validateSchema(invSchema, data)


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

    if func == "validate":
        out = validate(*params)
        return out
    elif func == "exec":
        out = execute(*params)
        return out
    elif func == "import":
        out = importer(*params)
        return out
    elif func == "publish":
        out = publish(*params)
        return out
    elif func == "invocation":
        out = invocation(*params)
        return out
    else:
        parser.print_help()
        raise SystemExit 
