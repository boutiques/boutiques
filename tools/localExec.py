#!/usr/bin/env python

import argparse, os, sys, json, random as rnd, string, math, subprocess, time, pwd

# Executor class
class LocalExecutor(object):
  """
  This class represents a json descriptor of a tool, and can execute various tasks related to it.
  It is constructed first via an input json descriptor file, which is held in the desc_dict field.

  An input can be added to it via the in_dict field, a dictionary from param ids to values.
  The in_dict field should only be modified via the public readInput method, which can either take
  a file (json or csv) or a string written in the command line. The field is always validated by checking
  the input parameters with respect to the descriptor.

  Other public methods include:
    execute - attempts to execute the tool described by the descriptor based on the current input (in in_dict)
    printCmdLine - simply prints the generated command line based on the current input values
    generateRandomParams - fills in_dict with random values (following the constraints of the descriptor schema)
  """

  # Constructor
  def __init__(self,desc,options={}):
    ## Initial parameters ##
    self.desc_path = desc  # Save descriptor path
    self.errs      = []    # Empty errors holder
    self.debug     = False # debug mode (also use python -u for unbuffered printing)
    ## Parse JSON descriptor ##
    with open(desc, 'r') as descriptor:
      self.desc_dict = json.loads( descriptor.read() )
    ## Helpers Functions ##
    # The set of input parameters from the json descriptor
    self.inputs     = self.desc_dict['inputs'] # Structure: [ {id:...},...,{id:...} ]
    # The set of parameter groups, according to the json descriptor
    self.groups     = self.desc_dict['groups'] if 'groups' in self.desc_dict.keys() else []
    # Retrieves the parameter corresponding to the given id
    self.byId       = lambda n: [ v for v in self.inputs if v['id']==n][0]
    # Retrieves the group corresponding to the given id
    self.byGid      = lambda g: [ v for v in self.groups if v['id']==g][0]
    # Retrieves the value of a field of an input from the descriptor. Returns None if not present.
    self.safeGet    = lambda i,k: None if not k in self.byId(i).keys() else self.byId(i)[k]
    # Retrieves the value of a field of a group from the descriptor. Returns None if not present.
    self.safeGrpGet = lambda g,k: None if not k in self.byGid(g).keys() else self.byGid(g)[k]
    # Retrieves the group a given parameter id belongs to; otherwise, returns None
    self.assocGrp   = lambda i: (filter( lambda g: i in g["members"], self.groups ) or [None])[0]
    # Returns the required inputs of a given input id, or the empty string
    self.reqsOf     = lambda t: self.safeGet(t,"requires-inputs") or []
    ## Container-image Options ##
    self.container = self.desc_dict.get('container-image')
    self.launchDir = None if self.container is None else self.container.get('working-directory')
    ## Extra Options ##
    # Include: forcePathType, ignoreContainer, and destroyTempScripts
    for option in options.keys(): setattr(self, option, options.get(option))
    # Container Implementation check
    if (not self.container is None) and self.container['type'] != 'docker':
      raise ValueError('Other container types than docker (e.g. ' + self.container['type'] + ') are not yet supported')

  # Attempt local execution of the command line generated from the input values
  def execute(self):

    '''
    The execute method runs the generated command line (from either generateRandomParams or readInput).
    If docker is specified, it will attempt to use it, instead of local execution.
    After execution, it checks for output file existence.
    '''

    command, exit_code, container = self.cmdLine[0], None, self.container or {}
    print('Attempting execution of command:\n\t' + command + '\n---/* Start program output */---')
    # Check for docker
    dockerImage, dockerIndex = container.get( 'image' ), container.get( 'index' )
    dockerIsPresent = (not dockerImage is None) and (not dockerIndex is None)
    # Export environment variables, if they are specified in the descriptor
    envVars = {}
    if 'environment-variables' in self.desc_dict.keys():
      for (envVarName,envVarValue) in [ (p['name'],p['value']) for p in self.desc_dict['environment-variables'] ]:
        os.environ[envVarName], envVars[envVarName] = envVarValue, envVarValue # for non-container and docker resp.
    # Docker script constant name
    # Note that docker cannot do a local volume mount of files starting with a '.', hence this one does not
    dsname = 'temp-' + str(int(time.time() * 1000)) + '.localExec.dockerjob.sh' # time tag to avoid overwrites
    # If docker is present, alter the command template accordingly
    if dockerIsPresent and not self.ignoreContainer:
      # Pull the docker image
      self._localExecute( "docker pull " + str(dockerImage) )
      # Generate command script
      uname, uid = pwd.getpwuid( os.getuid() )[ 0 ], str(os.getuid())
      # Adds the user to the container before executing the templated command line
      userchange = '' if not self.changeUser else ("useradd --uid " + uid + ' ' + uname + "\n")
      # If --changeUser was desired, run with su so that any output files are owned by the user instead of root
      if self.changeUser: command = 'su ' + uname + ' -c ' + "\"{0}\"".format(command)
      cmdString = "#!/bin/bash -l\n" + userchange + str( command )
      with open(dsname,"w") as scrFile: scrFile.write( cmdString )
      # Ensure the script is executable
      self._localExecute( "chmod 755 " + dsname )
      # Prepare extra environment variables
      envString = " "
      if envVars:
        for (key,val) in envVars.items(): envString += "-e " + str(key) + "=\'" + str(val) + '\' '
      # Change launch (working) directory if desired
      launchDir = '${PWD}' if (self.launchDir is None) else self.launchDir
      # Run it in docker
      dcmd = 'docker run --rm' + envString + ' -v ${PWD}:' + launchDir + ' -w ' + launchDir + ' ' + str(dockerImage) + ' ./' + dsname
      print('Executing in Docker via: ' + dcmd)
      exit_code = self._localExecute( dcmd )
    # Otherwise, just run command locally
    else:
      exit_code = self._localExecute( command )
    # Report exit status
    print('---/* End program output */---\nCompleted execution (exit code: ' + str(exit_code) + ')')
    time.sleep(0.5) # Give the OS a (half) second to finish writing
    # Destroy temporary docker script, if desired. By default, keep the script so the dev can look at it.
    if dockerIsPresent and self.destroyTempScripts:
      if os.path.isfile( dsname ): os.remove( dsname )
    # Check for output files (note: the path-template can contain command-line-keys
    print('Looking for output files:')
    for outfile in self.desc_dict['output-files']:
      # Generate correct path template based on input arguments
      template = outfile['path-template']
      for (input_id,input_key) in [(input['id'],input['command-line-key']) for input in self.inputs]:
        # Blanks are entered if template key is not present
        # Note: may wish to detect output files whose paths depend on particular inputs
        # and not search for them if the key is not present
        val = '' if not (input_id in self.in_dict.keys()) else self.in_dict[input_id]
        template = template.replace(input_key,val)
      # Alter the template if uses-absolute-path is specified
      # If it is, and the path is not already absolute, make it so
      if outfile.get('uses-absolute-path'):
        template = os.path.abspath(template)
      # Look for the target file
      exists = os.path.exists( template )
      # Note whether it could be found or not
      isOptional = outfile['optional'] if 'optional' in outfile.keys() else False
      s1 = 'Optional' if isOptional else 'Required'
      s2 = '' if exists else 'not '
      err = "Error! " if (not isOptional and not exists) else '' # Add error warning when required file is missing
      print("\t"+err+s1+" output file \'"+outfile['name']+"\' was "+s2+"found at "+template)

  # Private method that attempts to locally execute the given command. Returns the exit code.
  def _localExecute(self,command):
    try: # Note: invokes the command through the shell (potential injection dangers)
      process = subprocess.Popen( command , shell=True )
    except OSError as e:
      sys.stderr.write( 'OS Error during attempted execution!' )
      raise e
    except ValueError as e:
      sys.stderr.write( 'Input Value Error during attempted execution!' )
      raise e
    else:
      return process.wait()

  # Private method to generate a random input parameter set that follows the constraints from the json descriptor
  # This method fills in the in_dict field of the object with constrained random values
  def _randomFillInDict(self):
    ## Private helper functions for filling the dictionary ##
    # Helpers for generating random numbers, strings, etc...
    # Note: uses-absolute-path is satisfied for files by the automatic replacement in the _validateDict
    nd, nl   = 2, 5 # nd = number of random characters to use in generating strings, nl = max number of random list items
    randDigs = lambda: ''.join(rnd.choice(string.digits) for _ in range(nd)) # Generate random string of digits
    randFile = lambda: 'f_' + randDigs() + rnd.choice(['.csv','.tex','.j','.cpp','.m','.mnc','.nii.gz'])
    randStr  = lambda: 'str_' + ''.join(rnd.choice(string.digits+string.ascii_letters) for _ in range(nd))

    # A function for generating a number type parameter input
    # p is a dictionary object corresponding to a parameter description in the json descriptor
    # E.g. if p had no constraints from the json descriptor, the output would be a float in [defaultMin,defaultMax]
    #      if p had "integer": true, "minimum": 7, "maximum": 9, the output would be an int in [7,9]
    def randNum(p):
      param_id, defaultMin, defaultMax = p['id'], -50, 50
      isInt = self.safeGet( param_id , 'integer' ) # Check if the input parameter should be an int
      roundTowardsZero = lambda x: int(math.copysign(1,x) * int(abs(x)))
      # Assign random values to min and max, unless they have been specified
      minv, maxv = self.safeGet( param_id , 'minimum' ), self.safeGet( param_id , 'maximum' )
      if minv is None and maxv is None: minv, maxv = defaultMin, defaultMax
      elif minv is None and not (maxv is None): minv = maxv + defaultMin
      elif not (minv is None) and maxv is None: maxv = minv + defaultMax
      # Coerce the min/max to the proper number type
      if isInt: minv, maxv = roundTowardsZero(minv), roundTowardsZero(maxv)
      else: minv, maxv = float(minv), float(maxv)
      # Apply exclusive boundary constraints, if any
      if self.safeGet( param_id , 'exclusive-minimum' ): minv += (1 if isInt else 0.0001)
      if self.safeGet( param_id , 'exclusive-maximum' ): maxv -= (1 if isInt else 0.0001)
      # Returns a random int or a random float, depending on the type of p
      return (rnd.randint(minv,maxv) if isInt else round(rnd.uniform(minv,maxv),nd) )

    # Generate a random parameter value based on the input type (where prm \in self.inputs)
    def paramSingle(prm):
      if prm['type']=='Enum':   return rnd.choice( self.safeGet(prm['id'],'enum-value-choices') )
      if prm['type']=='File':   return randFile()
      if prm['type']=='String': return randStr()
      if prm['type']=='Number': return randNum(prm)
      if prm['type']=='Flag':   return rnd.choice(['true','false'])

    # For this function, given prm (a parameter description), a parameter value is generated
    # If prm is a list, a sequence of outputs is generated; otherwise, a single value is returned
    def makeParam(prm):
      mn = self.safeGet(prm['id'], 'min-list-entries') or 2
      mx = self.safeGet(prm['id'], 'max-list-entries') or nl
      isList = self.safeGet(prm['id'], 'list') or False
      return ' '.join(str(paramSingle(prm)) for _ in range(rnd.randint(mn,mx))) if isList else paramSingle(prm)

    # Returns a list of the ids of parameters that disable the input parameter
    def disablersOf( inParam ):
      return map(lambda disabler: disabler[0], # p[0] is the id of the disabling parameter
               filter(lambda disabler: inParam['id'] in disabler[1], # disabler[1] is the disables list
                 map(lambda prm: (prm['id'], self.safeGet(prm['id'],'disables-inputs') or []), self.inputs)
               )
             )

    # Returns the list of mutually requiring parameters of the target
    def mutReqs( targetParam ):
      return map(lambda mutualReq: self.byId( mutualReq[0] ), # Get object corresponding to id
               filter(lambda possibleMutReq: targetParam['id'] in possibleMutReq[1], # Keep requirements that require the target
                 map(lambda reqOfTarg: (reqOfTarg, self.reqsOf(reqOfTarg)), self.reqsOf(targetParam['id']))
               )
             )

    # Returns whether targ (an input parameter) has a value or is allowed to have one
    def isOrCanBeFilled( targ ):
      # If it is already filled in, report so
      if targ['id'] in self.in_dict.keys(): return True
      # If a disabler or a disabled target is already active, it cannot be filled
      for d in disablersOf( targ ) + (self.safeGet( targ['id'], 'disables-inputs' ) or []):
        if d in self.in_dict.keys(): return False
      # If at least one non-mutual requirement has not been met, it cannot be filled
      for r in self.reqsOf(targ['id']):
        if not r in self.in_dict: # If a requirement is not present
          if not targ['id'] in self.reqsOf(r): # and it is not mutually required
            return False
      # If it is in a mutex group with one target already chosen, it cannot be filled
      g = self.assocGrp( targ['id'] ) # Get the group that the target belongs to, if any
      if (not g is None) and self.safeGrpGet(g['id'],'mutually-exclusive'):
        if len(filter(lambda x: x in self.in_dict.keys(), g['members'])) > 0: return False
      return True

    # Handle the mutual requirement case by breadth first search in the graph of mutual requirements.
    # Essentially a graph is built, starting from targ (the target input parameter), where nodes are
    # input parameters and edges are a mutual requirement relation between nodes. BFS is used to check
    # every node, to see if can be (or has been) given a value. If all the nodes are permitted to be
    # given values, then they are all added at once; if even one of them cannot be given a value (e.g.
    # it has an active disabler) then none of the graph members can be added and so we just return false.
    #
    # Input: an input parameter from which to start building the graph
    # Output:
    #   Returns False if at least one of the mutual requirements cannot be met
    #   Returns a list of params to fill if all of them can be met (or [targ.id] if it has no mutReqs)
    def checkMutualRequirements(targ):
      checked, toCheck = [], [targ]
      while len(toCheck) > 0:
        current = toCheck.pop()
        checked.append( current )
        if not isOrCanBeFilled( current ): return False
        for mutreq in mutReqs( current ):
          if not mutreq['id'] in [c['id'] for c in checked]: toCheck.append(mutreq)
      return checked

    ## Start actual dictionary filling part ##
    # Clear the dictionary
    self.in_dict = {}
    # Fill in the required parameters
    for reqp in [r for r in self.inputs if self.safeGet(r['id'],'optional')==False]:
      self.in_dict[reqp['id']] = makeParam(reqp)
    # Fill in a random choice for each one-is-required group
    for grp in [g for g in self.groups if self.safeGrpGet(g['id'],'one-is-required')]:
      while True: # Loop to choose an allowed value, in case a previous choice disabled that one
        choice = self.byId( rnd.choice( grp['members'] ) ) # Pick a random parameter
        res = checkMutualRequirements( choice ) # see if it and its mutual requirements can be filled
        if res==False: continue # Try again if the chosen group member is not permissable
        for r in res: self.in_dict[r['id']] = makeParam(r)
        break # If we were allowed to add a parameter, we can stop
    # Choose a random number of times to try to fill optional inputs
    opts = [p for p in self.inputs if self.safeGet(p['id'],'') in [None,True]]
    # Loop a random number of times, each time attempting to fill a random parameter
    for _ in range(rnd.randint( len(opts) / 2 + 1, len(opts) * 2)):
      targ = rnd.choice( opts ) # Choose an optional output
      # If it is already filled in, continue
      if targ['id'] in self.in_dict.keys(): continue
      # If it is a prohibited option, continue (isFilled case handled above)
      if not isOrCanBeFilled(targ): continue
      # Now we handle the mutual requirements case. This is a little more complex because a mutual requirement
      # of targ can have its own mutual requirements, ad nauseam. We need to look at all of them recursively and either
      # fill all of them in (i.e. at once) or none of them (e.g. if one of them is disabled by some other param).
      result = checkMutualRequirements( targ )
      # Leave if the mutreqs cannot be satisfied
      if result == False: continue
      # Fill in the target(s) otherwise
      for r in result: self.in_dict[r['id']] = makeParam(r)

  # Function to generate random parameter values
  # This fills the in_dict with random values, validates the input, and generates the appropriate command line
  def generateRandomParams(self,n):

    '''
    The generateRandomParams method fills the in_dict field with randomly generated values following the schema.
    It then generates command line strings based on these values (more than 1 if -n was given).
    '''

    self.cmdLine = []
    for i in range(0,n):
      # Set in_dict with random values
      self._randomFillInDict()
      # Look at generated input, if debugging
      if self.debug: print( "Input: " + str( self.in_dict ) )
      # Check results (as much as possible)
      try: self._validateDict()
      # If an error occurs, print out the problems already encountered before blowing up
      except Exception: # Avoid catching BaseExceptions like SystemExit
        sys.stderr.write("An error occurred in validation\nPreviously saved issues\n")
        for err in self.errs: sys.stderr.write("\t" + str(err) + "\n")
        raise # Pass on (throw) the caught exception
      # Add new command line
      self.cmdLine.append( self._generateCmdLineFromInDict() )

  # Read in parameter input file or string
  def readInput(self,infile,stringInput):

    '''
    The readInput method sets the in_dict field of the executor object, based on a fixed input.
    It then generates a command line based on the input.

    infile: either the inputs in a file or the command-line string (from -s).
    stringInput: a boolean as to whether the method has been given a string or a file.
    '''

    # Quick check that the descriptor has already been read in
    assert self.desc_dict != None
    # String case
    if stringInput:
      instrings = [s.strip().split(",") for s in infile.split(";") if not s=='']
      self.in_dict = {v[0].strip() : v[1].strip() for v in instrings if len(v)==2}
    # File case
    else:
      # Read in input file (in_dict : id -> given value)
      with open(infile, 'r') as inparams:
        if infile.endswith('.csv'): # csv case
          lines = [ line.strip().split(",") for line in inparams.readlines() ]
          self.in_dict = { line[0].strip() : line[1].strip() for line in lines if len(line)==2}
        else: # json case
          ins = json.loads( inparams.read() )['inputs']
          self.in_dict = { d.keys()[0] : d.values()[0] for d in ins }
    # Input dictionary
    if self.debug: print( "Input: " + str( self.in_dict ) )
    # Fix special flag case: flags given the false value are treated as non-existent
    toRm = []
    for inprm in self.in_dict:
      if str(self.in_dict[inprm]).lower() == 'false' and self.byId(inprm)['type'] == 'Flag':
        toRm.append( inprm )
      elif self.byId(inprm)['type'] == 'Flag' and self.in_dict[inprm] == True:
        self.in_dict[inprm] = "true" # Fix json inputs using bools instead of strings
    for r in toRm: del self.in_dict[r]
    # Check results (as much as possible)
    try: self._validateDict()
    except Exception: # Avoid catching BaseExceptions like SystemExit
      sys.stderr.write("An error occurred in validation\nPreviously saved issues\n")
      for err in self.errs: sys.stderr.write("\t" + str(err) + "\n") # Write any errors we found
      raise # Raise the exception that caused failure
    # Build and save output command line (as a single-entry list)
    self.cmdLine = [ self._generateCmdLineFromInDict() ]

  # Private method to build the actual command line by substitution, using the input data
  def _generateCmdLineFromInDict(self):
    # Get the command line template
    template = self.desc_dict['command-line']
    # Substitute every given value into the template (incl. flags, flag-seps, ...)
    for paramId in map(lambda x: x['id'], self.inputs):
      clk = self.safeGet(paramId,'command-line-key')
      assert not clk is None, str(paramId) + ' does not appear to have a command-line-key'
      # Substitute into the template if a value was given
      if paramId in self.in_dict.keys():
        # Generate value to put in template
        flag   = self.safeGet(paramId,'command-line-flag') or ''
        sep    = self.safeGet(paramId,'command-line-flag-separator') or ' '
        inval  = self.in_dict[paramId]
        outval = flag + sep + str(inval)
        if self.safeGet(paramId,'type')=='Flag': # special case for flag-type inputs
          outval =  '' if inval.lower()=='false' else flag
        # Perform template substitution
        template = template.replace(clk, outval)
      # Wipe the cmd line key if the value was not given
      else:
        template = template.replace(clk, '')
    # Return substituted command line
    return template

  # Print the command line result
  def printCmdLine(self):
    print("Generated Command"+('s' if len(self.cmdLine)>1 else '')+':')
    for cmd in self.cmdLine: print(cmd)

  # Private method for validating input parameters
  def _validateDict(self):
    # Holder for errors
    self.errs = []
    # Return whether s is a proper number; if intCheck is true, also check if it is an int
    def isNumber(s,intCheck = False):
      try: int(s) if intCheck else float(s); return True
      except ValueError: return False
    # Check individual inputs
    for key in self.in_dict:
      isList = self.safeGet(key,"list")
      # Get current value and schema descriptor properties
      val, targ = self.in_dict[key], self.byId( key )
      # A little closure helper to check if input values satisy the json descriptor's constraints
      # Checks whether 'value' is appropriate for parameter 'input' by running 'isGood' on it
      # If the input parameter is bad, it adds 'msg' to the list of errors
      def check(keyname, isGood, msg, value): # Checks input values
        # No need to check constraints if they were not specified
        dontCheck = ((not keyname in targ.keys()) or (targ[keyname]==False))
        # Keyname = None is a flag to check the type
        if (not keyname is None) and dontCheck: return
        # The input function is used to check whether the input parameter is acceptable
        if not isGood(value, keyname):
          self.errs.append(key + ' (' + str(value) + ') ' + msg)
      # The id exists as an input and is not duplicate
      if len([ k for k in self.inputs if k['id']==key ]) != 1: self.errs.append(key+' is an invalid id')
      # Types are correct
      if targ["type"] == "Number":
        # Number type and constraints are not violated (note the lambda safety checks)
        for v in (str(val).split() if isList else [val]):
          check('minimum', lambda x,y: float(x) >= targ[y], "violates minimum value",v)
          check('exclusive-minimum', lambda x,y: float(x) > targ['minimum'], "violates exclusive min value",v)
          check('maximum', lambda x,y: float(x) <= targ[y], "violates maximum value",v)
          check('exclusive-maximum', lambda x,y: float(x) < targ['maximum'], "violates exclusive max value",v)
          check('integer', lambda x,y: isNumber(x,True), "violates integer requirement",v)
          check(None, lambda x,y: isNumber(x), "is not a number",v)
      elif targ["type"] == "Enum":
        # Enum value is in the list of allowed values
        check('enum-value-choices', lambda x,y: x in targ[y], "is not a valid enum choice",val)
      elif targ["type"] == "Flag":
        # Should be 'true' or 'false' when lower-cased (based on our transformations of the input)
        check(None, lambda x,y: x.lower() in ["true","false"], "is not a valid flag value",val)
      elif targ["type"] == "File":
        # Check path-type (absolute vs relative)
        if not self.forcePathType:
          for ftarg in (str(val).split() if isList else [val]):
            check('uses-absolute-path', lambda x,y: os.path.isabs(x), "is not an absolute path",ftarg)
        else:
          # Replace incorrectly specified paths if desired
          replacementFiles = []
          launchDir = self.launchDir if (not self.launchDir is None) else os.getcwd()
          for ftarg in (str(val).split() if isList else [val]):
            # Special case 1: launchdir is specified and we want to use absolute path
            # This is ignored when --ignoreContainer has been activated
            # Note: in this case, the pwd is mounted as the launchdir; we do not attempt to move files if they will not be mounted, currently
            # That is, specified files that are not in the pwd or a subfolder will not be mounted to the container
            if targ.get('uses-absolute-path') == True and (not self.launchDir is None) and (not self.ignoreContainer):
              relpath = os.path.relpath(ftarg, os.getcwd()) # relative path to target, from the pwd
              mountedAbsPath = os.path.join(launchDir,relpath) # absolute path in the container
              replacementFiles.append( os.path.abspath(mountedAbsPath) )
            # If the input uses-absolute-path, replace the path with its absolute version
            elif targ.get('uses-absolute-path') == True: replacementFiles.append( os.path.abspath(ftarg) )
          # Replace old val with the new one
          self.in_dict[ key ] = " ".join( replacementFiles )
      # List length constraints are satisfied
      if isList: check('min-list-entries', lambda x,y: len(x.split()) >= targ[y], "violates min size",val)
      if isList: check('max-list-entries', lambda x,y: len(x.split()) <= targ[y], "violates max size",val)
    # Required inputs are present
    for reqId in [v['id'] for v in self.inputs if not v.get('optional')]:
      if not reqId in self.in_dict.keys():
        self.errs.append('Required input ' + str(reqId) + ' is not present')
    # Disables/requires is satisfied
    for givenVal in [v for v in self.inputs if v['id'] in self.in_dict.keys()]:
      for r in self.reqsOf(givenVal['id']): # Check that requirements are present
        if not r in self.in_dict.keys():
          self.errs.append('Input '+str(givenVal['id'])+' is missing requirement '+str(r))
      for d in (givenVal['disables-inputs'] if 'disables-inputs' in givenVal.keys() else []):
        if d in self.in_dict.keys(): # Check if a disabler is present
          self.errs.append('Input '+str(d)+' should be disabled by '+str(givenVal['id']))
    # Group one-is-required/mutex is ok
    for group,mbs in map(lambda x: (x,x["members"]),self.groups):
      # Check that the set of parameters in mutually exclusive groups have at most one member present
      if ("mutually-exclusive" in group.keys()) and group["mutually-exclusive"]:
        if len(set.intersection( set(mbs) , set(self.in_dict.keys()) )) > 1:
          self.errs.append('Group ' + str(group["id"]) + ' is supposed to be mutex')
      # Check that the set of parameters in one-is-required groups have at least one member present
      if ("one-is-required" in group.keys()) and group["one-is-required"]:
        if len(set.intersection( set(mbs) , set(self.in_dict.keys()) )) < 1:
          self.errs.append('Group ' + str(group["id"]) + ' requires one member to be present')
    # Fast-fail if there was a problem with the input parameters
    if len(self.errs) != 0:
      sys.stderr.write("Problems found with prospective input:\n")
      for err in self.errs: sys.stderr.write("\t" + err + "\n")
      sys.exit(1)

# Execute program
if  __name__ == "__main__":

  # Parse arguments
  description = '''
A local tool executor to help test JSON descriptors for use in the Boutiques framework.
Should be used after successfully running validator.rb.

Program flow:
  - Requires a JSON descriptor of the tool, following the Boutiques schema.
  - Requires an input set of parameters. Can either:
    o Come from a .json file or .csv file [Specfied by --input/-i]
    o Be randomly generated based on the input json descriptor [Specified by --random/-r]
    o Be specifed on the command line itself [Specified by --string/-s]
  - The tool can then either:
    o Print the resulting command-line based on the input (to help check correctness of the permitted command lines) [Default behaviour]
    o Attempt to execute the command line output by the tool, for the given parameters (not for the random case) [--exec/-e flag]

Notes: validating the schema with a validator is recommended first. This script does not check the descriptor with respect to the schema.
       Only in the -e case are output files checked for, at the end. If docker is specified with -e, it will attempt to execute via docker.

Formats:
A .json input file should have an "inputs" array with one value per id, which should look like:
{
  "inputs" : [
    { "input_id_1" : "val1" },
    { "input_id_2" : "val2" },
    { "input_list" : "a b c" },
    { "input_flag" : "true" },
    ...
  ]
}

A .csv input file should look like the following:
input_id_1,val1
input_id_2,val2
input_list,a b c
input_flag,true
...

A string input should look like:
python localExec.py descriptor.json -s 'in_id_1,val_1;in_list,a b c;in_flag,true;in_id_2,val_2;...'

Notes: pass lists by space-separated values
       pass flags with 'true' or 'false' (false is the same as not including it)
       note the quotes in the -s input option
'''
  parser = argparse.ArgumentParser(description = description, formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('desc', metavar='descriptor', nargs = 1, help = 'The input JSON tool descriptor to test.')
  parser.add_argument('-i', '--input', help = 'Input parameter values with which to test the generation (.json or .csv).')
  parser.add_argument('-e', '--execute', action = 'store_true', help = 'Execute the program with the given inputs.')
  parser.add_argument('-r', '--random', action = 'store_true', help = 'Generate a random set of input parameters to check.')
  parser.add_argument('-n', '--num', type = int, help = 'Number of random parameter sets to examine.')
  parser.add_argument('-s', '--string', help = "Take as input a semicolon-separated string of comma-separated tuples on the command line.")
  parser.add_argument('--dontForcePathType', action = 'store_true', help = 'Fail if an input does not conform to absolute-path specification (rather than converting the path type).')
  parser.add_argument('--changeUser', action = 'store_true', help = 'Changes user in a container to the current user (prevents files generated from being owned by root)')
  parser.add_argument('--ignoreContainer', action = 'store_true', help = 'Attempt execution locally, even if a container is specified.')
  parser.add_argument('-d', '--destroyTempScripts', action = 'store_true', help = 'Destroys any temporary scripts used to execute commands in containers.')
  args = parser.parse_args()

  # Check arguments
  desc = args.desc[0]
  def errExit(msg, print_usage = True):
    if print_usage: parser.print_usage()
    sys.stderr.write('Error: ' + msg + '\n')
    sys.exit(1)
  given = lambda x: not (x is None)
  if given(args.num) and args.num < 1:
    errExit('--num was not given an appropriate value')
  elif given(args.num) and not args.random:
    errExit('--num requires random')
  elif args.random and args.execute:
    errExit('--random and --exec canot be used together')
  elif args.random and given(args.input):
    errExit('--random and --input cannot be used together')
  elif given(args.input) and not os.path.isfile( args.input ):
    errExit('The input file ' + str(args.input) + ' does not seem to exist', False)
  elif given(args.input) and not (args.input.endswith(".json") or args.input.endswith(".csv")):
    errExit('Input file ' + str(args.input) + ' must end in .json or .csv')
  elif args.execute and (not given(args.input) and not given(args.string)):
    errExit('--exec requires --input or --string be specified')
  elif not os.path.isfile( desc ):
    errExit('The input JSON descriptor does not seem to exist', False)
  elif not args.random and (not given(args.input) and not given(args.string)):
    errExit('The default mode requires an input (-i or -s)')
  elif args.random and given(args.string):
    errExit('--random and --string cannot be used together')
  elif given(args.num) and given(args.string):
    errExit('--num and --string cannot be used together')
  elif not given(args.num):
    args.num = 1

  # Prepare inputs
  inData = args.input if given(args.input) else ( args.string if given(args.string) else None )

  # Generate object that will perform the commands
  executor = LocalExecutor(desc, { 'forcePathType'      : not args.dontForcePathType,
                                   'destroyTempScripts' : args.destroyTempScripts,
                                   'ignoreContainer'    : args.ignoreContainer,
                                   'changeUser'         : args.changeUser              })

  ### Run the executor with the given parameters ###
  # Execution case
  if args.execute:
    # Read in given input
    executor.readInput(inData, given(args.string))
    # Execute it
    executor.execute()
  # Print random case
  elif args.random:
    # Generate random input
    executor.generateRandomParams(args.num)
    # Print the resulting command line
    executor.printCmdLine()
  # Print input case (default: no execution)
  else:
    # Read in given input
    executor.readInput(inData, given(args.string))
    # Print the resulting command line
    executor.printCmdLine()

