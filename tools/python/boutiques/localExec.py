#!/usr/bin/env python

import os
import sys
import simplejson as json
import random as rnd
import string
import math
import random
import subprocess
import time
import datetime
import hashlib
import os.path as op
from termcolor import colored
from boutiques.evaluate import evaluateEngine
from boutiques.logger import raise_error, print_info, print_warning
from boutiques.dataHandler import getDataCacheDir
from boutiques.util.utils import extractFileName, loadJson


class ExecutorOutput():

    def __init__(self, stdout, stderr, exit_code, desc_err,
                 output_files, missing_files, shell_command,
                 container_command,
                 container_location):
        try:
            self.stdout = decodeByteStr(stdout)
        except AttributeError as e:
            self.stdout = stdout
        try:
            self.stderr = decodeByteStr(stderr)
        except AttributeError as e:
            self.stderr = stderr
        self.exit_code = exit_code
        self.error_message = desc_err
        self.output_files = output_files
        self.missing_files = missing_files
        self.shell_command = shell_command
        self.container_command = container_command
        self.container_location = container_location

    def __str__(self):

        formatted_output_files = ""
        for f in self.output_files:
            if formatted_output_files != "":
                formatted_output_files += os.linesep
            formatted_output_files += ("\t- "+str(f))

        formatted_missing_files = ""
        for f in self.missing_files:
            if formatted_missing_files != "":
                formatted_missing_files += os.linesep
            formatted_missing_files += ("\t- "+str(f))

        def title(s):
            return colored(s + os.linesep, 'green')

        out = (title("Shell command") +
               "{0}" + os.linesep +
               title("Container location") +
               "{1}" + os.linesep +
               title("Container command") +
               "{2}" + os.linesep +
               title("Exit code") +
               "{3}" + os.linesep +
               (title("Std out") +
                "{4}" + os.linesep if self.stdout else "") +
               (title("Std err") +
                colored("{5}", 'red') + os.linesep if self.stderr else "") +
               title("Error message") +
               colored("{6}", 'red') + os.linesep +
               title("Output files") +
               "{7}" + os.linesep +
               title("Missing files") +
               colored("{8}", 'red') +
               os.linesep).format(self.shell_command,
                                  self.container_location,
                                  self.container_command,
                                  self.exit_code,
                                  self.stdout,
                                  self.stderr,
                                  self.error_message,
                                  formatted_output_files,
                                  formatted_missing_files)
        return out


class FileDescription():

    def __init__(self, boutiques_name, file_name, optional):
        self.boutiques_name = boutiques_name
        self.file_name = file_name
        self.optional = 'Optional'
        if not optional:
            self.optional = 'Required'

    def __str__(self):
        return "{0} ({1}, {2})".format(self.file_name, self.boutiques_name,
                                       self.optional)


class ExecutorError(Exception):
    pass


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
    def __init__(self, desc, invocation, options={}):
        # Initial parameters
        self.desc_path = desc    # Save descriptor path
        self.errs = []        # Empty errors holder
        self.invocation = invocation

        # Extra Options
        # Include: forcePathType and debug
        self.debug = False
        for option in list(options.keys()):
            setattr(self, option, options.get(option))

        # Parse JSON descriptor
        self.desc_dict = loadJson(desc, self.debug)

        # Set the shell
        self.shell = self.desc_dict.get("shell")
        if self.shell is None:
            self.shell = "/bin/sh"

        # Generate Summary for data collection
        if not self.skipDataCollect:
            self.summary = self._generateSummary(desc)

        # Helpers Functions
        # The set of input parameters from the json descriptor
        self.inputs = self.desc_dict['inputs']  # Struct: [{id:}..,{id:}]
        # The set of output parameters from the json descriptor
        self.outputs = self.desc_dict.get('output-files') or []
        # The set of parameter groups, according to the json descriptor
        self.groups = self.desc_dict.get('groups') or []

        # Container-image Options
        self.con = self.desc_dict.get('container-image')
        self.launchDir = None
        if self.con is not None:
            self.con.get('working-directory')

        # Generate the command line
        if self.invocation:
            self.readInput(self.invocation)

    # Retrieves the parameter corresponding to the given id
    def byId(self, n):
        return [v for v in self.inputs+self.outputs if v['id'] == n][0]

    # Retrieves the group corresponding to the given id
    def byGid(self, g):
        return [v for v in self.groups if v['id'] == g][0]

    # Retrieves the value of a field of an input
    # from the descriptor. Returns None if not present.
    def safeGet(self, i, k):
        if k not in list(self.byId(i).keys()):
            return None
        return self.byId(i)[k]

    # Retrieves the value of a field of a group from
    # the descriptor. Returns None if not present.
    def safeGrpGet(self, g, k):
        if k not in list(self.byGid(g).keys()):
            return None
        return self.byGid(g)[k]

    # Retrieves the group a given parameter id belongs to;
    # otherwise, returns None
    def assocGrp(self, i):
        return ([g for g in self.groups if i in g["members"]] or [None])[0]

    # Returns the required inputs of a given input id, or the empty string
    def reqsOf(self, t):
        return self.safeGet(t, "requires-inputs") or []

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
        command, exit_code, con = self.cmd_line[0], None, self.con or {}
        # Check for Container image
        conType, conImage = con.get('type'), con.get('image'),
        conIndex = con.get("index")
        conOpts = con.get("container-opts")
        conIsPresent = (conImage is not None)
        # Export environment variables, if they are specified in the descriptor
        envVars = {}
        if 'environment-variables' in list(self.desc_dict.keys()):
            variables = [(p['name'], p['value']) for p in
                         self.desc_dict['environment-variables']]
            for (envVarName, envVarValue) in variables:
                os.environ[envVarName] = envVarValue
                envVars[envVarName] = envVarValue
        # Container script constant name
        # Note that docker/singularity cannot do a local volume
        # mount of files starting with a '.', hence this one does not
        millitime = int(time.time()*1000)
        dsname = ('temp-' +
                  str(random.SystemRandom().randint(0, int(millitime))) +
                  "-" + str(millitime) + '.localExec.boshjob.sh')
        dsname = op.realpath(dsname)
        # If container is present, alter the command template accordingly
        container_location = ""
        container_command = ""
        if conIsPresent:
            # Figure out which container type to use
            conTypeToUse = self._chooseContainerTypeToUse(conType,
                                                          self.forceSingularity,
                                                          self.forceDocker)
            # Pull the container
            (conPath, container_location) = self.prepare(conTypeToUse)
            # Generate command script
            # Get the supported shell by the docker or singularity
            cmdString = "#!"+self.shell+" -l"+os.linesep+str(command)
            with open(dsname, "w") as scrFile:
                scrFile.write(cmdString)
            # Ensure the script is executable
            self._localExecute("chmod 755 " + dsname)
            # Prepare extra environment variables
            envString = ""
            if envVars:
                for (key, val) in list(envVars.items()):
                    envString += "SINGULARITYENV_{0}='{1}' ".format(key, val)
            # Change launch (working) directory if desired
            launchDir = self.launchDir
            if launchDir is None:
                launchDir = op.realpath('./')
            launchDir = op.realpath(launchDir)
            # Get the container options
            conOptsString = ""
            if conOpts:
                # Ignore container options if container type is not the one
                # specified in the descriptor.
                if conType != conTypeToUse:
                    print_warning("Ignoring incompatible container options.")
                else:
                    for opt in conOpts:
                        conOptsString += opt + ' '
            # Run it in docker
            mount_strings = [] if not mount_strings else mount_strings
            mount_strings = [op.realpath(m.split(":")[0])+":"+m.split(":")[1]
                             for m in mount_strings]
            mount_strings.append(op.realpath('./') + ':' + launchDir)
            if conTypeToUse == 'docker':
                envString = " "
                if envVars:
                    for (key, val) in list(envVars.items()):
                        envString += " -e {0}='{1}' ".format(key, val)
                # export mounts to docker string
                docker_mounts = " -v ".join(m for m in mount_strings)
                # If --changeUser was desired, provides the current user id
                # and its group id as the user and group to be used instead
                # of the default root within the container.
                userchange = ''
                if self.changeUser:
                    userchange = ' -u $(id -u):$(id -g)'

                container_command = ('docker run' + userchange +
                                     ' --entrypoint=' + self.shell +
                                     ' --rm' + envString +
                                     ' -v ' + docker_mounts +
                                     ' -w ' + launchDir + ' ' +
                                     conOptsString +
                                     str(conImage) + ' ' + dsname)
            elif conTypeToUse == 'singularity':
                envString = ""
                if envVars:
                    for (key, val) in list(envVars.items()):
                        envString += "SINGULARITYENV_{0}='{1}' ".format(key,
                                                                        val)
                singularity_mounts = '-B ' + ' '.join(mount_strings)
                container_command = (envString + 'singularity exec '
                                     '--cleanenv ' +
                                     singularity_mounts +
                                     ' -W ' + launchDir + ' ' +
                                     conOptsString +
                                     str(conPath) + ' ' + dsname)
            (stdout, stderr), exit_code = self._localExecute(container_command)
        # Otherwise, just run command locally
        else:
            (stdout, stderr), exit_code = self._localExecute(command)
        time.sleep(0.5)  # Give the OS a (half) second to finish writing

        # Destroy temporary docker script, if desired.
        # By default, keep the script so the dev can look at it.
        if conIsPresent and not self.debug:
            if os.path.isfile(dsname):
                os.remove(dsname)

        # Check for output files
        missing_files = []
        missing_files_dict = {}
        output_files = []
        output_files_dict = {}
        all_files = evaluateEngine(self, "output-files")
        required_files = evaluateEngine(self, "output-files/optional=False")
        optional_files = evaluateEngine(self, "output-files/optional=True")
        for f in all_files.keys():
            file_name = all_files[f]
            fd = FileDescription(f, file_name, False)
            if op.exists(file_name):
                output_files.append(fd)
                output_files_dict[f] = file_name
            else:  # file does not exist
                if f in required_files.keys():
                    missing_files.append(fd)
                    missing_files_dict[f] = file_name

        # Set error messages
        desc_err = ''
        if 'error-codes' in list(self.desc_dict.keys()):
            for err_elem in self.desc_dict['error-codes']:
                if err_elem['code'] == exit_code:
                    desc_err = err_elem['description']
                    break

        executor_output = ExecutorOutput(stdout,
                                         stderr,
                                         exit_code,
                                         desc_err,
                                         output_files,
                                         missing_files,
                                         command,
                                         container_command,
                                         container_location)

        if not self.skipDataCollect:
            # Generate public output
            self.public_out = self._generatePublicOutput(executor_output,
                                                         output_files_dict,
                                                         missing_files_dict)
            # Write data collection to file
            self._saveDataCaptureToCache()

        return executor_output

    # Looks for the container image locally and pulls it if not found
    # Returns a tuple containing the container filename (for Singularity)
    # and the container location (local or pulled)
    def prepare(self, conTypeToUse=None):
        con = self.con
        if con is None:
            return ("", "Descriptor does not specify a container image.")

        conType, conImage = con.get('type'), con.get('image'),
        conIndex = con.get("index")

        # If container is present, alter the command template accordingly
        conName = ""

        if conTypeToUse is None:
            conTypeToUse = self._chooseContainerTypeToUse(conType)

        if conTypeToUse == 'docker':
            # Pull the docker image
            if self._localExecute("docker pull " + str(conImage))[1]:
                container_location = "Local copy"
            else:
                container_location = "Pulled from Docker"
            return (conName, container_location)

        elif conTypeToUse == 'singularity':
            if not conIndex:
                conIndex = "shub://"
            elif not conIndex.endswith("://"):
                conIndex = conIndex + "://"

            if self.imagePath:
                conName = op.basename(self.imagePath)
                imageDir = op.normpath(op.dirname(self.imagePath))
            else:
                conName = conImage.replace("/", "-").replace(":", "-") + ".simg"
                imageDir = op.normpath("")

            # Check if container already exists
            if self._singConExists(conName, imageDir):
                conPath = op.abspath(op.join(imageDir, conName))
                return conPath, "Local ({0})".format(conName)

            # Container does not exist, try to pull it
            if self.imagePath:
                lockDir = self.imagePath + "-lock"
            else:
                lockDir = conName + "-lock"

            maxcount = 36
            count = 0

            while count < maxcount:
                count += 1
                try:
                    os.mkdir(lockDir)
                except OSError:
                    time.sleep(5)
                else:
                    try:
                        # Check if container was created while waiting
                        if self._singConExists(conName, imageDir):
                            conPath = op.abspath(op.join(imageDir, conName))
                            container_location = "Local ({0})".format(conName)
                        # Container still does not exist, so pull it
                        else:
                            conPath, container_location = self._pullSingImage(
                                conName, conIndex, conImage, imageDir, lockDir)
                        return conPath, container_location
                    finally:
                        self._cleanUpAfterSingPull(lockDir)
            # If loop times out, check again for existence, otherwise
            # raise an error
            if self._singConExists(conName, imageDir):
                conPath = op.abspath(op.join(imageDir, conName))
                return conPath, "Local ({0})".format(conName)
            raise_error(ExecutorError, "Unable to retrieve Singularity "
                        "image.")

    # Private method that checks if a Singularity image exists locally
    def _singConExists(self, conName, imageDir):
        return conName in os.listdir(imageDir)

    # Private method that pulls a Singularity image
    def _pullSingImage(self, conName, conIndex, conImage, imageDir, lockDir):
        # Give the file a temporary name while it's building
        conNameTmp = conName + ".tmp"
        # Set the pull directory to the specified imagePath
        if self.imagePath:
            os.environ["SINGULARITY_PULLFOLDER"] = imageDir
        pull_loc = "\"{0}\" {1}{2}".format(conNameTmp,
                                           conIndex,
                                           conImage)
        container_location = ("Pulled from {1}{2} ({0} not found "
                              "in current working "
                              "directory or specified "
                              "image path)").format(conName,
                                                    conIndex,
                                                    conImage)
        # Pull the singularity image
        sing_command = "singularity pull --name " + pull_loc
        (stdout, stderr), return_code = self._localExecute(
                                                sing_command)
        if return_code:
            message = ("Could not pull Singularity"
                       " image: " + os.linesep + " * Pull command: " +
                       sing_command + os.linesep + " * Error: " +
                       stderr.decode("utf-8"))
            raise_error(ExecutorError, message)
        os.rename(op.join(imageDir, conNameTmp), op.join(imageDir, conName))
        conPath = op.abspath(op.join(imageDir, conName))
        return conPath, container_location

    # Removes the lock directory and environment variable
    # created while pulling an image
    def _cleanUpAfterSingPull(self, lockDir):
        os.rmdir(lockDir)
        if "SINGULARITY_PULLFOLDER" in os.environ:
            del os.environ["SINGULARITY_PULLFOLDER"]

    def _isDockerInstalled(self):
        return not subprocess.Popen("type docker", shell=True).wait()

    # Chooses whether to use Docker or Singularity based on the
    # descriptor, executor options and if Docker is installed.
    def _chooseContainerTypeToUse(self, conType, forceSing=False,
                                  forceDocker=False):
        if (self._isDockerInstalled() and
                (conType == 'docker' and not forceSing or
                 forceDocker)):
            return "docker"
        else:
            return "singularity"

    # Private method that attempts to locally execute the given
    # command. Returns the exit code.
    def _localExecute(self, command):
        # Note: invokes the command through the shell
        # (potential injection dangers)
        if self.debug:
            print_info("Running: {0}".format(command))
        try:
            if self.stream:
                process = subprocess.Popen(command, shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)
            else:
                process = subprocess.Popen(command, shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)

        except OSError as e:
            sys.stderr.write('OS Error during attempted execution!')
            raise e
        except ValueError as e:
            sys.stderr.write('Input Value Error during attempted execution!')
            raise e

        if not self.stream:
            return process.communicate(), process.returncode

        while True:
            if process.poll() is not None:
                break
            outLine = process.stdout.readline().decode()
            if outLine != '':
                sys.stdout.write(outLine)
        # Return (stdout, stderr) as (None, None) since it was already
        # printed in real time
        return (None, None), process.returncode

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
        # number_decimals = the number of decimal places to round to
        # on randomly generated floating point numbers
        number_decimals = 3
        # epsilon = an upper bound on the relative error due to
        # rounding for the chosen number of decimals, making sure
        # excluded values aren't rounded to by accident.
        epsilon = 1.0/(10**number_decimals)

        def randDigs():
            # Generate random string of digits
            return ''.join(rnd.choice(string.digits)
                           for _ in range(nd))

        def randFile(id):
            return ('f_' + id + '_' + randDigs() +
                    rnd.choice(['.csv', '.tex', '.j',
                                '.cpp', '.m', '.mnc',
                                '.nii.gz', '']))

        def randStr(id):
            return 'str_' + id + '_' + ''.join(rnd.choice(string.digits +
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
            isInt = self.safeGet(param_id, 'integer')

            def roundTowardsZero(x):
                return int(math.copysign(1, x) * int(abs(x)))
            # Assign random values to min and max,
            # unless they have been specified
            minv = self.safeGet(param_id, 'minimum')
            maxv = self.safeGet(param_id, 'maximum')
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
            if self.safeGet(param_id, 'exclusive-minimum'):
                minv += 1 if isInt else epsilon
            if self.safeGet(param_id, 'exclusive-maximum'):
                maxv -= 1 if isInt else epsilon
            # Returns a random int or a random float, depending on the type of p
            return (rnd.randint(minv, maxv)
                    if isInt else round(rnd.uniform(minv, maxv),
                                        number_decimals))

        # Generate a random parameter value based on the input
        # type (where prm \in self.inputs)
        def paramSingle(prm):
            if self.safeGet(prm['id'], 'value-choices'):
                return rnd.choice(self.safeGet(prm['id'], 'value-choices'))
            if prm['type'] == 'String':
                return randStr(prm['id'])
            if prm['type'] == 'Number':
                return randNum(prm)
            if prm['type'] == 'Flag':
                return rnd.choice([True, False])
            if prm['type'] == 'File':
                return randFile(prm['id'])

        # For this function, given prm (a parameter description),
        # a parameter value is generated
        # If prm is a list, a sequence of outputs is generated;
        # otherwise, a single value is returned
        def makeParam(prm):
            mn = self.safeGet(prm['id'], 'min-list-entries') or 2
            mx = self.safeGet(prm['id'], 'max-list-entries') or nl
            isList = self.safeGet(prm['id'], 'list') or False
            return [paramSingle(prm) for _ in
                    range(rnd.randint(mn, mx))] if isList else paramSingle(prm)

        # Returns a list of the ids of parameters that
        # disable the input parameter
        def disablersOf(inParam):
            return [disabler[0] for disabler in
                    [disabler for disabler in
                     [(prm['id'], self.safeGet(prm['id'],
                                               'disables-inputs') or [])
                      for prm in self.inputs] if inParam['id'] in disabler[1]]]

        # Returns the list of mutually requiring parameters of the target
        def mutReqs(targetParam):
            return [self.byId(mutualReq[0]) for mutualReq in
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
            for d in disablersOf(targ) + (self.safeGet(
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
            g = self.assocGrp(targ['id'])
            if (g is not None) and self.safeGrpGet(g['id'],
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
        # Fill in the parameters depending on require complete
        for params in [r for r in self.inputs
                       if not r.get('optional') or self.requireComplete]:
            self.in_dict[params['id']] = makeParam(params)
            # Check for mutex between in_dict and last in param
            for group, mbs in [(x, x["members"]) for x in self.groups
                               if x.get('mutually-exclusive')]:
                if len(set.intersection(set(mbs),
                                        set(self.in_dict.keys()))) > 1:
                    # Delete last in param
                    del self.in_dict[params['id']]

        # Fill in a random choice for each one-is-required group
        for grp in [g for g in self.groups
                    if self.safeGrpGet(g['id'], 'one-is-required')]:
            # Loop to choose an allowed value,
            # in case a previous choice disabled that one
            while True:
                # Pick a random parameter
                choice = self.byId(rnd.choice(grp['members']))
                # see if it and its mutual requirements can be filled
                res = checkMutualRequirements(choice)
                if res is False:
                    # Try again if the chosen group member is not permissible
                    continue
                for r in res:
                    self.in_dict[r['id']] = makeParam(r)
                break  # If we were allowed to add a parameter, we can stop
        # Choose a random number of times to try to fill optional inputs
        opts = [p for p in self.inputs
                if self.safeGet(p['id'], '') in [None, True]]
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
                if self.requireComplete is None or self.requireComplete:
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

        self.cmd_line = []
        for i in range(0, n):
            # Set in_dict with random values
            self._randomFillInDict()
            # Look at generated input, if debugging
            if self.debug:
                print_info("Input: " + str(self.in_dict))
            # Check results (as much as possible)
            try:
                self._validateDict()
            # If an error occurs, print out the problems already
            # encountered before blowing up
            except Exception as e:  # Avoid BaseExceptions like SystemExit
                sys.stderr.write("An error occurred in validation\n"
                                 "Previously saved issues\n")
                for err in self.errs:
                    sys.stderr.write("\t" + str(err) + "\n")
                raise e  # Pass on (throw) the caught exception
            # Add new command line
            self.cmd_line.append(self._generateCmdLineFromInDict())

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
        self.in_dict = loadJson(infile)

        # Input dictionary
        if self.debug:
            print_info("Input: " + str(self.in_dict))

        # Generate public invocation
        if not self.skipDataCollect:
            self.public_in = self._generatePublicInvocation()

        # Add default values for required parameters,
        # if no value has been given
        addDefaultValues(self.desc_dict, self.in_dict)
        # Check results (as much as possible)
        try:
            self._validateDict()
        except Exception:  # Avoid catching BaseExceptions like SystemExit
            sys.stderr.write("An error occurred in validation\n"
                             "Previously saved issues\n")
            for err in self.errs:
                # Write any errors we found
                sys.stderr.write("\t" + str(err) + "\n")
            raise  # Raise the exception that caused failure
        # Build and save output command line (as a single-entry list)
        self.cmd_line = [self._generateCmdLineFromInDict()]

    # Private method to replace the keys in template by input and output
    # values. Input and output values are looked up in self.in_dict and
    # self.out_dict
    # * if use_flags is true, keys will be replaced by:
    #      * flag+flag-separator+value if flag is not None
    #      * value otherwise
    # * if unfound_keys is "remove", unfound keys will be replaced by ""
    # * if unfound_keys is "clear" then the template is cleared if it has
    #     unfound keys (useful for configuration files)
    # * before being substituted, the values will be:
    #     * stripped from all the strings in stripped_extensions
    #     * escaped for special characters
    def _replaceKeysInTemplate(self, template,
                               use_flags=False, unfound_keys="remove",
                               stripped_extensions=[],
                               escape_special_chars=True):

        def escape_string(s):
            try:
                from shlex import quote
            except ImportError as e:
                from pipes import quote
            return quote(s)

        # Concatenate input and output dictionaries
        in_out_dict = dict(self.in_dict)
        in_out_dict.update(self.out_dict)
        # Go through all the keys
        for param_id in [x['id'] for x in self.inputs + self.outputs]:
            escape = (escape_special_chars and
                      (self.safeGet(param_id, 'type') == 'String' or
                       self.safeGet(param_id, 'type') == 'File') or
                      param_id in self.out_dict.keys())
            clk = self.safeGet(param_id, 'value-key')
            if clk is None:
                continue
            if param_id in list(in_out_dict.keys()):  # param has a value
                val = in_out_dict[param_id]
                if type(val) is list:
                    s_val = ""
                    list_sep = self.safeGet(param_id, 'list-separator')
                    if list_sep is None:
                        list_sep = " "
                    for x in val:
                        s = str(x)
                        if escape:
                            s = escape_string(str(x))
                        if val.index(x) == len(val)-1:
                            s_val += s
                        else:
                            s_val += s + list_sep
                    val = s_val
                elif escape:
                    val = escape_string(val)
                # Add flags and separator if necessary
                flag = self.safeGet(param_id, 'command-line-flag')
                if (use_flags and flag is not None):
                    sep = self.safeGet(param_id,
                                       'command-line-flag-separator')
                    if sep is None:
                        sep = ' '
                    # special case for flag-type inputs
                    if self.safeGet(param_id, 'type') == 'Flag':
                        val = '' if val is False else flag
                    else:
                        val = flag + sep + str(val)
                # Remove file extensions from input value
                if (self.safeGet(param_id, 'type') == 'File' or
                        self.safeGet(param_id, 'type') == 'String'):
                    for extension in stripped_extensions:
                        val = val.replace(extension, "")
                # Here val can be a number so we need to cast it
                template = template.replace(clk, str(val))
            else:  # param has no value
                if unfound_keys == "remove":
                    template = template.replace(clk, '')
                elif unfound_keys == "clear":
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
                outputFileName = self.safeGet(outputId, 'path-template')
            stripped_extensions = self.safeGet(
                                        outputId,
                                        "path-template-stripped-extensions")
            if stripped_extensions is None:
                stripped_extensions = []
            # We keep the unfound keys because they will be
            # substituted in a second call to the method in case
            # they are output keys
            outputFileName = self._replaceKeysInTemplate(outputFileName,
                                                         False,
                                                         "keep",
                                                         stripped_extensions,
                                                         False)
            if self.safeGet(outputId, 'uses-absolute-path'):
                outputFileName = os.path.abspath(outputFileName)
            self.out_dict[outputId] = outputFileName

    # Private method to write configuration files
    # Configuration files are output files that have a file-template
    def _writeConfigurationFiles(self):
        for outputId in [x['id'] for x in self.outputs]:
            fileTemplate = self.safeGet(outputId, 'file-template')
            if fileTemplate is None:
                continue  # this is not a configuration file
            stripped_extensions = self.safeGet(
                                        outputId,
                                        "path-template-stripped-extensions")
            if stripped_extensions is None:
                stripped_extensions = []
            # We substitute the keys line by line so that we can
            # clear the lines that have keys with no value
            # (undefined optional params)
            newTemplate = []
            for line in fileTemplate:
                newTemplate.append(self._replaceKeysInTemplate(
                                                line,
                                                False, "clear",
                                                stripped_extensions,
                                                True))
            template = os.linesep.join(newTemplate)
            # Write the configuration file
            fileName = self.out_dict[outputId]
            dirs = os.path.dirname(fileName)
            if dirs and not os.path.exists(dirs):
                os.makedirs(dirs)
            file = open(fileName, 'w')
            file.write(template)
            file.close()

    # Private method to build the actual command line by substitution,
    # using the input data
    def _generateCmdLineFromInDict(self):
        # Generate output file names
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
        template = self._replaceKeysInTemplate(template, True,
                                               "remove", [], True)
        # Return substituted command line
        return template

    # Print the command line result
    def printCmdLine(self):
        print("Generated Command" +
              ('s' if len(self.cmd_line) > 1 else '') + ':')
        for cmd in self.cmd_line:
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
            isList = self.safeGet(key, "list")
            # Get current value and schema descriptor properties
            val, targ = self.in_dict[key], self.byId(key)

            # A little closure helper to check if input values satisfy
            # the json descriptor's constraints
            # Checks whether 'value' is appropriate for parameter
            # 'input' by running 'isGood' on it
            # If the input parameter is bad, it adds 'msg' to the list of errors
            def check(keyname, isGood, msg, value):  # Checks input values
                # No need to check constraints if they were not specified
                dontCheck = ((keyname not in list(targ.keys())) or
                             (targ[keyname] is False))
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
                for v in (val if isList else [val]):
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
            elif self.safeGet(targ['id'], 'value-choices'):
                # Value is in the list of allowed values
                if isinstance(val, list):
                    fn = (lambda x, y: all([x1 in targ[y] for x1 in x]))
                else:
                    fn = (lambda x, y: x in targ[y])
                check('value-choices', fn,
                      "is not a valid enum choice", val)
            elif targ["type"] == "Flag":
                # Should be 'true' or 'false' when lower-cased
                # (based on our transformations of the input)
                check(None,
                      lambda x, y: type(x) == bool,
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
                    for ftarg in (val if isList else [val]):
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
                        else:
                            replacementFiles.append(ftarg)
                    # Replace old val with the new one
                    if len(replacementFiles) == 1:
                        self.in_dict[key] = replacementFiles[0]
                    else:
                        self.in_dict[key] = replacementFiles
            # List length constraints are satisfied
            if isList:
                check('min-list-entries',
                      lambda x, y: len(x) >= targ[y],
                      "violates min size", val)
            if isList:
                check('max-list-entries',
                      lambda x, y: len(x) <= targ[y],
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
        for group, mbs in [(x, x["members"]) for x in self.groups]:
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
            message = "Problems found with prospective input:\n"
            for err in self.errs:
                message += ("\t" + err + "\n")
            raise_error(ExecutorError, message)

    # Private method to generate summary object of data
    # collection file containing the tool name and descriptor DOI
    def _generateSummary(self, desc):
        summary = {}
        summary['name'] = self.desc_dict['name']
        summary['descriptor-doi'] = self._findDOI(desc)
        return summary

    # Private method to attempt to find descriptor DOI
    # through various cases
    # userInput may be json string, filename or zenodo id
    def _findDOI(self, userIn):
        doi_prefix = "10.5281/"
        # DOI in Zenodo reference case
        if userIn.split(".")[0].lower() == "zenodo":
            return doi_prefix+userIn
        # File cases
        if os.path.isfile(userIn):
            # Most recent DOI in file if user is publisher
            # Include check to ensure descriptor is unmodified
            if self.desc_dict.get('doi') is not None:
                doi = self.desc_dict.get('doi')
                if loadJson(doi) == self.desc_dict:
                    return doi
            # DOI in filename if descriptor pulled from Zenodo
            # Include check to ensure descriptor is as published
            elif os.path.basename(userIn).split("-")[0].lower() == "zenodo":
                doi = os.path.basename(userIn).split(".")[0].replace("-", ".")
                if loadJson(doi) == self.desc_dict:
                    return doi_prefix+doi
        # No DOI found, save descriptor to cache and return filename
        return self._saveDescriptorToCache()

    # Private method to generate public invocation object
    # for data collection file
    # absolute paths are stripped to filenames and hashes are generated for
    # each input of type File, all other inputs are recorded as submitted
    def _generatePublicInvocation(self):
        public_in_dict = self.in_dict.copy()
        # Replace file type inputs with object containing
        # input file hash and filename
        for x in self.inputs:
            if x.get('type') == "File":
                id = x.get('id')
                path = public_in_dict.get(id)
                if path is not None:
                    if isinstance(path, list):
                        public_in_dict[id] = [self._buildPublicFile(p)
                                              for p in path]
                    else:
                        public_in_dict[id] = self._buildPublicFile(path)

        return public_in_dict

    # Private method to generate public output object for data collection file
    # hashes are generated for each output file.
    def _generatePublicOutput(self,
                              exec_output,
                              out_files_dict,
                              missing_files_dict):
        public_out_dict = {}
        public_out_dict['stdout'] = exec_output.stdout
        public_out_dict['stderr'] = exec_output.stderr
        public_out_dict['exit-code'] = exec_output.exit_code
        public_out_dict['error-message'] = exec_output.error_message
        public_out_dict['shell-command'] = exec_output.shell_command
        public_out_dict['missing-files'] = missing_files_dict

        # Iterate through output files to generate output objects
        # and generate objects with hash of files
        out_files_dict = {id: self._buildPublicFile(filename)
                          for id, filename in out_files_dict.items()}
        public_out_dict['output-files'] = out_files_dict
        return public_out_dict

    # Private method to recursively explore directory and hash all files
    def _buildPublicFile(self, path):
        filename = extractFileName(path)
        # If path is not found, report it
        if not os.path.exists(path):
            return {'file-name': filename, 'not_found': True}
        # Directories are expanded recursively
        if os.path.isdir(path):
            contents = os.listdir(path)
            # Recursive call to expand directory
            files = [self._buildPublicFile(os.path.join(path, x))
                     for x in contents]
            return {'file-name': filename, 'files': files}
        # Files are hashed
        else:
            md5sum = computeMD5(path)
            return {'file-name': filename, 'md5sum': md5sum}

    # Private method to publish data collection objects to file
    # summary, publicInput an publicOutput are combined and
    # written to a file in .cache
    def _saveDataCaptureToCache(self):
        date_time = datetime.datetime.now().isoformat()
        tool_name = self.summary['name'].replace(' ', '-')
        self.summary['date-time'] = date_time
        # Combine three modules in master dictionary
        data_dict = {'summary': self.summary,
                     'public-invocation': self.public_in,
                     'public-output': self.public_out}
        # Convert dictionary to Json string
        content = json.dumps(data_dict, indent=4)
        # Write collected data to file
        data_cache_dir = getDataCacheDir()
        filename = "{0}_{1}.json".format(tool_name, date_time)
        file_path = os.path.join(data_cache_dir, filename)
        file = open(file_path, 'w+')
        file.write(content)
        file.close()
        if self.debug:
            print_info("Data capture from execution saved to cache as {}"
                       .format(filename))

    # Local function handles case where descriptor is not published
    # Checks if descriptor already saved to cache, if not then saves
    # copy for future publication
    def _saveDescriptorToCache(self):
        tool_name = self.desc_dict.get('name').replace(' ', '-')
        data_cache_dir = getDataCacheDir()
        data_cache_files = os.listdir(data_cache_dir)
        # Filter for descriptors in cache with the same tool name to check
        # if descriptor already in cache
        matching_files = [x for x in data_cache_files
                          if len(x.split("_")) > 1 and
                          x.split("_")[1] is tool_name.replace(' ', '-')]
        match = None
        for fl in matching_files:
            path = os.path.join(data_cache_dir, fl)
            file_dict = loadJson(path)
            if file_dict == self.desc_dict:
                match = fl
                break
        if match:
            if self.debug:
                print_info("Unpublished descriptor match found in data cache "
                           "as {}".format(match))
            return match
        # Write descriptor to data cache and save return filename
        content = json.dumps(self.desc_dict, indent=4)
        date_time = datetime.datetime.now().isoformat()
        filename = "descriptor_{0}_{1}.json".format(tool_name, date_time)
        path = os.path.join(data_cache_dir, filename)
        file = open(path, 'w+')
        file.write(content)
        file.close()
        if self.debug:
            print_info("Descriptor from execution saved to cache for future "
                       "publishing as {}".format(filename))
        return filename


# Adds default values to input dictionary
# for parameters whose values were not given
def addDefaultValues(desc_dict, in_dict):
    inputs = desc_dict['inputs']
    for in_param in [s for s in inputs
                     if s.get("default-value") is not None]:
        if in_dict.get(in_param['id']) is None:
            in_dict[in_param['id']] = in_param.get("default-value")
    return in_dict


# Parses absolute path into filename
def extractFileName(path):
    # Helps OS path handle case where "/" is at the end of path
    if path is None:
        return None
    elif path[:-1] == '/':
        return os.path.basename(path[:-1]) + "/"
    else:
        return os.path.basename(path)


# Hashes files with MD5,
# capable of handling large data files
def computeMD5(filepath):
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as fhandle:
        for chunk in iter(lambda: fhandle.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# Decodes a byte string, handling non utf-8 characters according to
# Python version.
def decodeByteStr(byteStr):
    if sys.version_info[0] < 3:
        # ignore non-decodable chars
        return byteStr.decode("utf=8", "ignore")
    elif sys.version_info[0] == 3 and sys.version_info[1] == 4:
        # replace non-decodable chars with a replacement character
        return byteStr.decode("utf=8", "replace")
    else:
        # replace non-decodable chars with escape sequence
        return byteStr.decode("utf=8", "backslashreplace")
