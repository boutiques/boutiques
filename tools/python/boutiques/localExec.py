#!/usr/bin/env python

import argparse
import os
import sys
import json
import random as rnd
import string
import math
import random
import subprocess
import time
import pwd
import os.path as op


# Executor class
class LocalExecutor(object):
    """
    This class represents a json descriptor of a tool, and can execute
    various tasks related to it. It is constructed first via an
    input json descriptor file, which is held in the desc_dict field.

    An input can be added to it via the in_dict field, a dictionary from
    param ids to values. The in_dict field should only be modified
    via the public readInput method, which can either take
    a file (json or csv) or a string written in the command line.
    The field is always validated by checking the input parameters
     with respect to the descriptor.

    Other public methods include:
        execute - attempts to execute the tool described by the descriptor
            based on the current input (in in_dict)
        printCmdLine - simply prints the generated command line
            based on the current input values
        generateRandomParams - fills in_dict with random values
            (following the constraints of the descriptor schema)
    """

    # Constructor
    def __init__(self, desc, options={}):
        # Initial parameters
        self.desc_path = desc    # Save descriptor path
        self.errs = []        # Empty errors holder
        self.debug = False  # debug mode (also use python -u)
        # Parse JSON descriptor
        with open(desc, 'r') as descriptor:
            self.desc_dict = json.loads(descriptor.read())
        # Helpers Functions
        # The set of input parameters from the json descriptor
        self.inputs = self.desc_dict['inputs']  # Struct: [{id:}..,{id:}]
        # The set of output parameters from the json descriptor
        self.outputs = self.desc_dict['output-files']  # Struct: [{id:}..,{id:}]
        # The set of parameter groups, according to the json descriptor
        self.groups = []
        if 'groups' in list(self.desc_dict.keys()):
            self.groups = self.desc_dict['groups']

        # Retrieves the parameter corresponding to the given id
        def byId(n):
            return [v for v in self.inputs+self.outputs if v['id'] == n][0]

        # Retrieves the group corresponding to the given id
        def byGid(g):
            return [v for v in self.groups if v['id'] == g][0]

        # Retrieves the value of a field of an input
        # from the descriptor. Returns None if not present.
        def safeGet(i, k):
            if k not in list(byId(i).keys()):
                return None
            return byId(i)[k]

        # Retrieves the value of a field of a group from
        # the descriptor. Returns None if not present.
        def safeGrpGet(g, k):
            if k not in list(byGId(g).keys()):
                return None
            return byGId(g)[k]

        # Retrieves the group a given parameter id belongs to;
        # otherwise, returns None
        def assocGrp(i):
            return ([g for g in self.groups if i in g["members"]] or [None])[0]

        # Returns the required inputs of a given input id, or the empty string
        def reqsOf(t):
                return safeGet(t, "requires-inputs") or []

        # Container-image Options
        self.con = self.desc_dict.get('container-image')
        self.launchDir = None
        if self.con is not None:
            self.con.get('working-directory')

        # Extra Options
        # Include: forcePathType and destroyTempScripts
        for option in list(options.keys()):
            setattr(self, option, options.get(option))
        # Container Implementation check
        conEngines = ['docker', 'singularity']
        if (self.con is not None) and self.con['type'] not in conEngines:
                msg = "Other container types than {} (e.g. {})"
                " are not yet supported"
                raise ValueError(msg.format(", ".join(conEngines),
                                            self.con['type']))

    # Attempt local execution of the command line
    # generated from the input values
    def execute(self, mount_strings):
        '''
        The execute method runs the generated command line
        (from either generateRandomParams or readInput)
        If docker is specified, it will attempt to use it, instead
        of local execution.
        After execution, it checks for output file existence.
        '''
        command, exit_code, con = self.cmdLine[0], None, self.con or {}
        print('Attempting execution of command:\n\t' + command +
              '\n---/* Start program output */---')
        # Check for Container image
        conType, conImage, conIndex = con.get('type'), con.get('image'),
        con.get("index")
        conIsPresent = (conImage is not None)
        # Export environment variables, if they are specified in the descriptor
        envVars = {}
        if 'environment-variables' in list(self.desc_dict.keys()):
            variables = [(p['name'], p['value']) for p in
                         self.desc_dict['environment-variables']]
            for (envVarName, envVarValue) in variables:
                os.environ[envVarName], envVars[envVarName] = envVarValue,
                envVarValue
        # Container script constant name
        # Note that docker/singularity cannot do a local volume
        # mount of files starting with a '.', hence this one does not
        millitime = int(time.time()*1000)
        dsname = ('temp-' +
                  str(random.SystemRandom().randint(0, int(millitime))) +
                  "-" + str(millitime) + '.localExec.boshjob.sh')
        dsname = op.realpath(dsname)
        # If container is present, alter the command template accordingly
        if conIsPresent:
            if conType == 'docker':
                # Pull the docker image
                if self._localExecute("docker pull " + str(conImage))[1]:
                    print("Container not found online - trying local copy")
            elif conType == 'singularity':
                if not conIndex:
                    conIndex = "shub://"
                elif not conIndex.endswith("://"):
                    conIndex = conIndex + "://"
                conName = conImage.replace("/", "-") + ".simg"

                if conName not in os.listdir('./'):
                    print(os.listdir('./'))
                    # Pull the singularity image
                    if self._localExecute("singularity pull --name"
                                          " \"{}\" {}{}".format(conName,
                                                                conIndex,
                                                                conImage))[1]:
                        print("Container not found online - trying local copy")
                conName = op.abspath(conName)
            else:
                print('Unrecognized container type: \"%s\"' % conType)
                sys.exit(1)
            # Generate command script
            uname, uid = pwd.getpwuid(os.getuid())[0], str(os.getuid())
            # Adds the user to the container before executing
            # the templated command line
            userchange = '' if not self.changeUser else ("useradd --uid " +
                                                         uid + ' ' + uname +
                                                         "\n")
            # If --changeUser was desired, run with su so that
            # any output files are owned by the user instead of root
            # Get the supported shell by the docker or singularity
            if self.changeUser:
                command = 'su ' + uname + ' -c ' + "\"{0}\"".format(command)
            cmdString = "#!/bin/sh -l\n" + userchange + str(command)
            with open(dsname, "w") as scrFile:
                scrFile.write(cmdString)
            # Ensure the script is executable
            self._localExecute("chmod 755 " + dsname)
            # Prepare extra environment variables
            envString = " "
            if envVars:
                for (key, val) in list(envVars.items()):
                    envString += "-e " + str(key) + "=\'" + str(val) + '\' '
            # Change launch (working) directory if desired
            launchDir = self.launchDir
            if launchDir is None:
                launchDir = op.realpath('./')
            launchDir = op.realpath(launchDir)
            # Run it in docker
            mount_strings = [] if not mount_strings else mount_strings
            mount_strings = [op.realpath(m.split(":")[0])+":"+m.split(":")[1]
                             for m in mount_strings]
            mount_strings.append(op.realpath('./') + ':' + launchDir)
            if conType == 'docker':
                # export mounts to docker string
                docker_mounts = " -v ".join(m for m in mount_strings)
                dcmd = ('docker run --entrypoint=/bin/sh --rm' + envString +
                        ' -v ' + docker_mounts + ' -w ' + launchDir + ' ' +
                        str(conImage) + ' ' + dsname)
            elif conType == 'singularity':
                singularity_mounts = " -B ".join(m for m in mount_strings)
                # TODO: Test singularity runtime on cluster
                dcmd = ('singularity exec' + envString + ' -B ' +
                        singularity_mounts + ' -W ' + launchDir + ' ' +
                        str(conName) + ' ' + dsname)
            else:
                print('Unrecognized container type: \"%s\"' % conType)
                sys.exit(1)
            print('Executing via: ' + dcmd)
            (stdout, stderr), exit_code = self._localExecute(dcmd)
        # Otherwise, just run command locally
        else:
            (stdout, stderr), exit_code = self._localExecute(command)
        # Report exit status
        print('---/* Begin program output */---')
        if stdout != '':
            print(stdout.decode('utf-8'))
        print('---/* End program output */---\nCompleted execution'
              ' (exit code: ' + str(exit_code) + ')')
        time.sleep(0.5)  # Give the OS a (half) second to finish writing
        # Destroy temporary docker script, if desired.
        # By default, keep the script so the dev can look at it.
        if conIsPresent and self.destroyTempScripts:
            if os.path.isfile(dsname):
                os.remove(dsname)
        # Check for output files (note: the path-template
        # can contain value-keys)
        print('Looking for output files:')
        for outfile in self.desc_dict['output-files']:
            outFileName = self.out_dict[outfile['id']]
            # Look for the target file
            exists = os.path.exists(outFileName)
            # Note whether it could be found or not
            if 'optional' in list(outfile.keys()):
                isOptional = outfile['optional']
            else:
                isOptional = False
            s1 = 'Optional' if isOptional else 'Required'
            s2 = '' if exists else 'not '
            err = ''
            if (not isOptional and not exists):
                err = "Error! "
            # Add error warning when required file is missing
            print("\t" + err + s1 + " output file \'" + outfile['name'] +
                  "\' was " + s2 + "found at " + outFileName)
        desc_err = ''
        if 'error-codes' in list(self.desc_dict.keys()):
            for err_elem in self.desc_dict['error-codes']:
                if err_elem['code'] == exit_code:
                        desc_err = err_elem['description']
                        break
        error_msg = ''
        if stderr != b'':
            error_msg = 'Execution ERR ({0}): {1}'.format(exit_code, stderr)
        if desc_err != '':
            error_msg += '{0}{1} ERR ({2}): {3}'.format('\n' if
                                                        error_msg != '' else
                                                        '',
                                                        self.desc_dict['name'],
                                                        exit_code, desc_err)

        return stdout, stderr, exit_code, error_msg

    # Private method that attempts to locally execute the given
    # command. Returns the exit code.
    def _localExecute(self, command):
        # Note: invokes the command through the shell
        # (potential injection dangers)
        try:
            process = subprocess.Popen(command, shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

        except OSError as e:
            sys.stderr.write('OS Error during attempted execution!')
            raise e
        except ValueError as e:
            sys.stderr.write('Input Value Error during attempted execution!')
            raise e
        else:
            return process.communicate(), process.returncode

    # Private method to generate a random input parameter set that follows
    # the constraints from the json descriptor
    # This method fills in the in_dict field of the object
    # with constrained random values
    def _randomFillInDict(self):
        # Private helper functions for filling the dictionary
        # Helpers for generating random numbers, strings, etc...
        # Note: uses-absolute-path is satisfied for files by the
        # automatic replacement in the _validateDict
        # nd = number of random characters to use in generating strings,
        # nl = max number of random list items
        nd, nl = 2, 5

        def randDigs():
            # Generate random string of digits
            return ''.join(rnd.choice(string.digits)
                           for _ in range(nd))

        def randFile():
            return ('f_' + randDigs() +
                    rnd.choice(['.csv', '.tex', '.j',
                                '.cpp', '.m', '.mnc',
                                '.nii.gz']))

        def randStr():
            return 'str_' + ''.join(rnd.choice(string.digits +
                                    string.ascii_letters)
                                    for _ in range(nd))

        # A function for generating a number type parameter input
        # p is a dictionary object corresponding to a parameter
        # description in the json descriptor
        # E.g. if p had no constraints from the json descriptor,
        # the output would be a float in [defaultMin,defaultMax]
        #            if p had "integer": true, "minimum": 7,
        # "maximum": 9, the output would be an int in [7,9]
        def randNum(p):
            param_id, defaultMin, defaultMax = p['id'], -50, 50
            # Check if the input parameter should be an int
            isInt = safeGet(param_id, 'integer')

            def roundTowardsZero(x):
                return int(math.copysign(1, x) * int(abs(x)))
            # Assign random values to min and max,
            # unless they have been specified
            minv, maxv = safeGet(param_id, 'minimum'),
            safeGet(param_id, 'maximum')
            if minv is None and maxv is None:
                minv, maxv = defaultMin, defaultMax
            elif minv is None and not (maxv is None):
                minv = maxv + defaultMin
            elif not (minv is None) and maxv is None:
                maxv = minv + defaultMax
            # Coerce the min/max to the proper number type
            if isInt:
                minv, maxv = roundTowardsZero(minv), roundTowardsZero(maxv)
            else:
                minv, maxv = float(minv), float(maxv)
            # Apply exclusive boundary constraints, if any
            if safeGet(param_id, 'exclusive-minimum'):
                minv += (1 if isInt else 0.0001)
            if safeGet(param_id, 'exclusive-maximum'):
                maxv -= (1 if isInt else 0.0001)
            # Returns a random int or a random float, depending on the type of p
            return (rnd.randint(minv, maxv)
                    if isInt else round(rnd.uniform(minv, maxv), nd))

        # Generate a random parameter value based on the input
        # type (where prm \in self.inputs)
        def paramSingle(prm):
            if safeGet(prm['id'], 'value-choices'):
                return rnd.choice(safeGet(prm['id'], 'value-choices'))
            if prm['type'] == 'String':
                return randStr()
            if prm['type'] == 'Number':
                return randNum(prm)
            if prm['type'] == 'Flag':
                return rnd.choice(['true', 'false'])
            if prm['type'] == 'File':
                return randFile()

        # For this function, given prm (a parameter description),
        # a parameter value is generated
        # If prm is a list, a sequence of outputs is generated;
        # otherwise, a single value is returned
        def makeParam(prm):
            mn = safeGet(prm['id'], 'min-list-entries') or 2
            mx = safeGet(prm['id'], 'max-list-entries') or nl
            isList = safeGet(prm['id'], 'list') or False
            return ' '.join(str(paramSingle(prm)) for _ in
                            range(rnd.randint(mn, mx))
                            ) if isList else paramSingle(prm)

        # Returns a list of the ids of parameters that
        # disable the input parameter
        def disablersOf(inParam):
            return [disabler[0] for disabler in
                    [disabler for disabler in
                     [(prm['id'], safeGet(prm['id'],
                                               'disables-inputs') or [])
                      for prm in self.inputs] if inParam['id'] in disabler[1]]]

        # Returns the list of mutually requiring parameters of the target
        def mutReqs(targetParam):
            return [byId(mutualReq[0]) for mutualReq in
                    [possibleMutReq for possibleMutReq in
                     [(reqOfTarg, self.reqsOf(reqOfTarg)) for reqOfTarg in
                         self.reqsOf(targetParam['id'])]
                     if targetParam['id'] in possibleMutReq[1]]]

        # Returns whether targ (an input parameter) has a
        # value or is allowed to have one
        def isOrCanBeFilled(targ):
            # If it is already filled in, report so
            if targ['id'] in list(self.in_dict.keys()):
                return True
            # If a disabler or a disabled target is already active,
            # it cannot be filled
            for d in disablersOf(targ) + (safeGet(
                                                 targ['id'],
                                                 'disables-inputs') or []):
                if d in list(self.in_dict.keys()):
                    return False
            # If at least one non-mutual requirement has
            # not been met, it cannot be filled
            for r in self.reqsOf(targ['id']):
                if r not in self.in_dict:  # If a requirement is not present
                    # and it is not mutually required
                    if targ['id'] not in self.reqsOf(r):
                        return False
            # If it is in a mutex group with one target already chosen,
            # it cannot be filled
            # Get the group that the target belongs to, if any
            g = assocGrp(targ['id'])
            if (g is not None) and safeGrpGet(g['id'],
                                                   'mutually-exclusive'):
                if len([x for x in g['members']
                        if x in list(self.in_dict.keys())]) > 0:
                    return False
            return True

        # Handle the mutual requirement case by breadth first search in
        # the graph of mutual requirements. Essentially a graph is built,
        # starting from targ (the target input parameter), where nodes
        # are input parameters and edges are a mutual requirement
        # relation between nodes. BFS is used to check every node, to see
        # if can be (or has been) given a value. If all the nodes are
        # permitted to be given values, then they are all added at once;
        # if even one of them cannot be given a value (e.g. it has an
        # active disabler) then none of the graph members can be added
        # and so we just return false. # Input: an input parameter from
        # which to start building the graph Output: Returns False if at
        # least one of the mutual requirements cannot be met Returns a
        # list of params to fill if all of them can be met (or [targ.id]
        # if it has no mutReqs)
        def checkMutualRequirements(targ):
            checked, toCheck = [], [targ]
            while len(toCheck) > 0:
                current = toCheck.pop()
                checked.append(current)
                if not isOrCanBeFilled(current):
                    return False
                for mutreq in mutReqs(current):
                    if not mutreq['id'] in [c['id'] for c in checked]:
                        toCheck.append(mutreq)
            return checked

        # Start actual dictionary filling part
        # Clear the dictionary
        self.in_dict = {}
        # Fill in the required parameters
        for reqp in [r for r in self.inputs if not r.get('optional')]:
            print(reqp['id'])
            self.in_dict[reqp['id']] = makeParam(reqp)
        # Fill in a random choice for each one-is-required group
        for grp in [g for g in self.groups
                    if safeGrpGet(g['id'], 'one-is-required')]:
            # Loop to choose an allowed value,
            # in case a previous choice disabled that one
            while True:
                # Pick a random parameter
                choice = byId(rnd.choice(grp['members']))
                # see if it and its mutual requirements can be filled
                res = checkMutualRequirements(choice)
                if res is False:
                    # Try again if the chosen group member is not permissable
                    continue
                for r in res:
                    self.in_dict[r['id']] = makeParam(r)
                break  # If we were allowed to add a parameter, we can stop
        # Choose a random number of times to try to fill optional inputs
        opts = [p for p in self.inputs
                if safeGet(p['id'], '') in [None, True]]
        # Loop a random number of times, each time
        #  attempting to fill a random parameter
        for _ in range(rnd.randint(int(len(opts) / 2 + 1), len(opts) * 2)):
            targ = rnd.choice(opts)  # Choose an optional output
            # If it is already filled in, continue
            if targ['id'] in list(self.in_dict.keys()):
                continue
            # If it is a prohibited option, continue
            # (isFilled case handled above)
            if not isOrCanBeFilled(targ):
                continue
            # Now we handle the mutual requirements case. This is a little
            # more complex because a mutual requirement
            # of targ can have its own mutual requirements, ad nauseam.
            # We need to look at all of them recursively and either
            # fill all of them in (i.e. at once) or none of them
            # (e.g. if one of them is disabled by some other param).
            result = checkMutualRequirements(targ)
            # Leave if the mutreqs cannot be satisfied
            if result is False:
                continue
            # Fill in the target(s) otherwise
            for r in result:
                self.in_dict[r['id']] = makeParam(r)

    # Function to generate random parameter values
    # This fills the in_dict with random values, validates the input,
    # and generates the appropriate command line
    def generateRandomParams(self, n):

        '''
        The generateRandomParams method fills the in_dict field
        with randomly generated values following the schema.
        It then generates command line strings based on these
        values (more than 1 if -n was given).
        '''

        self.cmdLine = []
        for i in range(0, n):
            # Set in_dict with random values
            self._randomFillInDict()
            # Look at generated input, if debugging
            if self.debug:
                print("Input: " + str(self.in_dict))
            # Check results (as much as possible)
            try:
                self._validateDict()
            # If an error occurs, print out the problems already
            # encountered before blowing up
            except Exception:  # Avoid catching BaseExceptions like SystemExit
                sys.stderr.write("An error occurred in validation\n"
                                 "Previously saved issues\n")
                for err in self.errs:
                    sys.stderr.write("\t" + str(err) + "\n")
                raise  # Pass on (throw) the caught exception
            # Add new command line
            self.cmdLine.append(self._generateCmdLineFromInDict())

    # Read in parameter input file or string
    def readInput(self, infile):

        '''
        The readInput method sets the in_dict field of the executor
        object, based on a fixed input.
        It then generates a command line based on the input.

        infile: either the inputs in a file or
        the command-line string (from -s).
        stringInput: a boolean as to whether the method has
        been given a string or a file.
        '''

        # Quick check that the descriptor has already been read in
        assert self.desc_dict is not None
        with open(infile, 'r') as inparams:
            self.in_dict = json.loads(inparams.read())
        # Input dictionary
        if self.debug:
            print("Input: " + str(self.in_dict))
        # Fix special flag case: flags given the false value
        # are treated as non-existent
        toRm = []
        for inprm in self.in_dict:
            if (str(self.in_dict[inprm]).lower() == 'false'
               and byId(inprm)['type'] == 'Flag'):
                    toRm.append(inprm)
            elif (byId(inprm)['type'] == 'Flag'
                  and self.in_dict[inprm] is True):
                # Fix json inputs using bools instead of strings
                self.in_dict[inprm] = "true"
        for r in toRm:
            del self.in_dict[r]
        # Add default values for required parameters,
        # if no value has been given
        for input in [s for s in self.inputs
                      if s.get("default-value") is not None
                      and not s.get("optional")]:
            if self.in_dict.get(input['id']) is None:
                df = input.get("default-value")
                if not input['type'] == 'Flag':
                    self.in_dict[input['id']] = df
                else:
                    self.in_dict[input['id']] = str(df)
        # Check results (as much as possible)
        try:
            pass  # self._validateDict()
        except Exception:  # Avoid catching BaseExceptions like SystemExit
            sys.stderr.write("An error occurred in validation\n"
                             "Previously saved issues\n")
            for err in self.errs:
                # Write any errors we found
                sys.stderr.write("\t" + str(err) + "\n")
            raise  # Raise the exception that caused failure
        # Build and save output command line (as a single-entry list)
        self.cmdLine = [self._generateCmdLineFromInDict()]

    # Private method to replace the keys in template by input and output
    # values. Input and output values are looked up in self.in_dict and
    # self.out_dict
    # * if useFlags is true, keys will be replaced by flag+flag-separator+value
    # * if unfoundKeys is "remove", unfound keys will be replaced by ""
    # * if unfoundKeys is "clear" then the template is cleared if it has
    #     unfound keys (useful for configuration files)
    # * before being substituted, the keys will be stripped from all
    #    the strings in strippedExtensions
    def _replaceKeysInTemplate(self, template,
                               useFlags=False, unfoundKeys="remove",
                               strippedExtensions=[]):
            # Concatenate input and output dictionaries
            in_out_dict = dict(self.in_dict)
            in_out_dict.update(self.out_dict)
            # Go through all the keys
            for paramId in [x['id'] for x in self.inputs + self.outputs]:
                clk = safeGet(paramId, 'value-key')
                if clk is None:
                    continue
                if paramId in list(in_out_dict.keys()):  # param has a value
                    val = in_out_dict[paramId]
                    if type(val) is list:
                        s_val = ""
                        for x in val:
                            s_val += str(x) + " "
                        val = s_val
                    else:
                            val = str(val)
                    # Add flags and separator if necessary
                    if useFlags:
                        flag = safeGet(paramId, 'command-line-flag') or ''
                        sep = safeGet(paramId,
                                           'command-line-flag-separator') or ' '
                        val = flag + sep + val
                        # special case for flag-type inputs
                        if safeGet(paramId, 'type') == 'Flag':
                            val = '' if val.lower() == 'false' else flag
                    # Remove file extensions from input value
                    for extension in strippedExtensions:
                        val = val.replace(extension, "")
                    template = template.replace(clk, val)
                else:  # param has no value
                    if unfoundKeys == "remove":
                        template = template.replace(clk, '')
                    elif unfoundKeys == "clear":
                        if clk in template:
                            return ""
            return template

    # Private method to generate output file names.
    # Output file names will be put in self.out_dict.
    def _generateOutputFileNames(self):
        if not hasattr(self, 'out_dict'):
            # a dictionary that will contain the output file names
            self.out_dict = {}
        for outputId in [x['id'] for x in self.outputs]:
            # Initialize file name with path template or existing value
            if outputId in list(self.out_dict.keys()):
                outputFileName = self.out_dict[outputId]
            else:
                outputFileName = safeGet(outputId, 'path-template')
            strippedExtensions = safeGet(
                                        outputId,
                                        "path-template-stripped-extensions")
            if strippedExtensions is None:
                strippedExtensions = []
            # We keep the unfound keys because they will be
            # substituted in a second call to the method in case
            # they are output keys
            outputFileName = self._replaceKeysInTemplate(outputFileName,
                                                         False,
                                                         "keep",
                                                         strippedExtensions)
            if safeGet(outputId, 'uses-absolute-path'):
                outputFileName = os.path.abspath(outputFileName)
            self.out_dict[outputId] = outputFileName

    # Private method to write configuration files
    # Configuration files are output files that have a file-template
    def _writeConfigurationFiles(self):
        for outputId in [x['id'] for x in self.outputs]:
            fileTemplate = safeGet(outputId, 'file-template')
            if fileTemplate is None:
                continue  # this is not a configuration file
            strippedExtensions = safeGet(
                                        outputId,
                                        "path-template-stripped-extensions")
            if strippedExtensions is None:
                strippedExtensions = []
            # We substitute the keys line by line so that we can
            # clear the lines that have keys with no value
            # (undefined optional params)
            newTemplate = []
            for line in fileTemplate:
                newTemplate.append(self._replaceKeysInTemplate(
                                                line,
                                                False, "clear",
                                                strippedExtensions))
            template = "\n".join(newTemplate)
            # Write the configuration file
            fileName = self.out_dict[outputId]
            file = open(fileName, 'w')
            file.write(template)
            file.close()

    # Private method to build the actual command line by substitution,
    # using the input data
    def _generateCmdLineFromInDict(self):
        # Genrate output file names
        self._generateOutputFileNames()
        # it is required to call the method twice in case path
        # templates contain output keys
        self._generateOutputFileNames()
        # Write configuration files
        self._writeConfigurationFiles()
        # Get the command line template
        template = self.desc_dict['command-line']
        # Substitute every given value into the template
        # (incl. flags, flag-seps, ...)
        template = self._replaceKeysInTemplate(template, True, "remove")
        # Return substituted command line
        return template

    # Print the command line result
    def printCmdLine(self):
        print("Generated Command" +
              ('s' if len(self.cmdLine) > 1 else '') + ':')
        for cmd in self.cmdLine:
            print(cmd)

    # Private method for validating input parameters
    def _validateDict(self):
        # Holder for errors
        self.errs = []

        # Return whether s is a proper number; if intCheck is true,
        # also check if it is an int
        def isNumber(s, intCheck=False):
            try:
                int(s) if intCheck else float(s)
                return True
            except ValueError:
                return False
        # Check individual inputs
        for key in self.in_dict:
            isList = safeGet(key, "list")
            # Get current value and schema descriptor properties
            val, targ = self.in_dict[key], byId(key)

            # A little closure helper to check if input values satisfy
            # the json descriptor's constraints
            # Checks whether 'value' is appropriate for parameter
            # 'input' by running 'isGood' on it
            # If the input parameter is bad, it adds 'msg' to the list of errors
            def check(keyname, isGood, msg, value):  # Checks input values
                # No need to check constraints if they were not specified
                dontCheck = ((keyname not in list(targ.keys()))
                             or (targ[keyname] is False))
                # Keyname = None is a flag to check the type
                if (keyname is not None) and dontCheck:
                    return
                # The input function is used to check whether
                # the input parameter is acceptable
                if not isGood(value, keyname):
                    self.errs.append(key + ' (' + str(value) + ') ' + msg)
            # The id exists as an input and is not duplicate
            if len([k for k in self.inputs if k['id'] == key]) != 1:
                self.errs.append(key+' is an invalid id')
            # Types are correct
            if targ["type"] == "Number":
                # Number type and constraints are not violated
                # (note the lambda safety checks)
                for v in (str(val).split() if isList else [val]):
                    check('minimum', lambda x, y: float(x) >= targ[y],
                          "violates minimum value", v)
                    check('exclusive-minimum',
                          lambda x, y: float(x) > targ['minimum'],
                          "violates exclusive min value", v)
                    check('maximum', lambda x, y: float(x) <= targ[y],
                          "violates maximum value", v)
                    check('exclusive-maximum',
                          lambda x, y: float(x) < targ['maximum'],
                          "violates exclusive max value", v)
                    check('integer', lambda x, y: isNumber(x, True),
                          "violates integer requirement", v)
                    check(None, lambda x, y: isNumber(x), "is not a number", v)
            elif safeGet(targ['id'], 'value-choices'):
                # Value is in the list of allowed values
                check('value-choices', lambda x, y: x in targ[y],
                      "is not a valid enum choice", val)
            elif targ["type"] == "Flag":
                # Should be 'true' or 'false' when lower-cased
                # (based on our transformations of the input)
                check(None,
                      lambda x, y: x.lower() in ["true", "false"],
                      "is not a valid flag value", val)
            elif targ["type"] == "File":
                # Check path-type (absolute vs relative)
                if not self.forcePathType:
                    for ftarg in (str(val).split() if isList else [val]):
                        check('uses-absolute-path',
                              lambda x, y: os.path.isabs(x),
                              "is not an absolute path", ftarg)
                else:
                    # Replace incorrectly specified paths if desired
                    replacementFiles = []
                    launchDir = os.getcwd()
                    if self.launchDir is not None:
                        launchDir = self.launchDir
                    for ftarg in (str(val).split() if isList else [val]):
                        # Special case 1: launchdir is specified and we
                        # want to use absolute path
                        # Note: in this case, the pwd is mounted as the
                        # launchdir; we do not attempt to move files if they
                        # will not be mounted, currently
                        # That is, specified files that are not in the pwd or a
                        # subfolder will not be mounted to the container
                        if (targ.get('uses-absolute-path') is True and
                           self.launchDir is not None):
                            # relative path to target, from the pwd
                            relpath = os.path.relpath(ftarg, os.getcwd())
                            # absolute path in the container
                            mountedAbsPath = os.path.join(launchDir, relpath)
                            replacementFiles.append(
                                        os.path.abspath(mountedAbsPath))
                        # If the input uses-absolute-path, replace
                        # the path with its absolute version
                        elif targ.get('uses-absolute-path') is True:
                            replacementFiles.append(os.path.abspath(ftarg))
                    # Replace old val with the new one
                    self.in_dict[key] = " ".join(replacementFiles)
            # List length constraints are satisfied
            if isList:
                check('min-list-entries',
                      lambda x, y: len(x.split()) >= targ[y],
                      "violates min size", val)
            if isList:
                check('max-list-entries',
                      lambda x, y: len(x.split()) <= targ[y],
                      "violates max size", val)
        # Required inputs are present
        for reqId in [v['id'] for v in self.inputs if not v.get('optional')]:
            if reqId not in list(self.in_dict.keys()):
                self.errs.append('Required input ' + str(reqId) +
                                 ' is not present')
        # Disables/requires is satisfied
        for givenVal in [v for v in self.inputs
                         if v['id'] in list(self.in_dict.keys())]:
            # Check that requirements are present
            for r in self.reqsOf(givenVal['id']):
                if r not in list(self.in_dict.keys()):
                    self.errs.append('Input ' + str(givenVal['id']) +
                                     ' is missing requirement '+str(r))
            for d in (givenVal['disables-inputs']
                      if 'disables-inputs' in list(givenVal.keys()) else []):
                # Check if a disabler is present
                if d in list(self.in_dict.keys()):
                    self.errs.append('Input ' + str(d) +
                                     ' should be disabled by ' +
                                     str(givenVal['id']))
        # Group one-is-required/mutex is ok
        for group, bmbs in [(x, x["members"]) for x in self.groups]:
            # Check that the set of parameters in mutually
            # exclusive groups have at most one member present
            if (("mutually-exclusive" in list(group.keys())) and
               group["mutually-exclusive"]):
                if len(set.intersection(set(mbs),
                                        set(self.in_dict.keys()))) > 1:
                    self.errs.append('Group ' + str(group["id"]) +
                                     ' is supposed to be mutex')
            # Check that the set of parameters in one-is-required
            # groups have at least one member present
            if (("one-is-required" in list(group.keys())) and
               group["one-is-required"]):
                    if len(set.intersection(set(mbs),
                                            set(self.in_dict.keys()))) < 1:
                        self.errs.append('Group ' + str(group["id"]) +
                                         ' requires one member to be present')
        # Fast-fail if there was a problem with the input parameters
        if len(self.errs) != 0:
            sys.stderr.write("Problems found with prospective input:\n")
            for err in self.errs:
                sys.stderr.write("\t" + err + "\n")
            sys.exit(1)
