#!/usr/bin/env python

'''
A local tool executor to help test JSON descriptors for use in the Boutiques framework.
Should be used after successfully running validator.rb.

Program flow:
  - Requires a JSON descriptor of the tool, following the Boutiques schema.
  - Requires an input set of parameters. Can either:
    o Come from a .json file or .csv file [Specfied by --input/-i]
    o Be randomly generated based on the input json descriptor [Specified by --random/-r]
  - The tool can then either:
    o Print the resulting command-line based on the input (to help check correctness of the permitted command lines) [Default behaviour]
    o Attempt to execute the command line output by the tool, for the given parameters (not for the random case) [--exec/-e flag]

Note: validating the schema with a validator is recommended first. This script does not check the descriptor with respect to the schema.
      Only in the -e case are output files checked for, at the end

Formats:
A .json input file should look like:
{
  "inputs" : [
    { "input_id_1" : "val1" },
    { "input_id_2" : "val2" },
    ...
  ]
}

A .csv input file should look like:
input_id_1,val1
input_id_2,val2
...

Notes: pass lists by space-separated values
       pass flags with 'true' or 'false' (false is the same as not including it)

'''

import argparse, os, sys, json, random as rnd, string, math, subprocess, time

# Executor class
class LocalExecutor(object):

  # Constructor
  def __init__(self,desc):
    self.desc_path = desc  # Save descriptor path
    self.errs      = []    # Empty errors holder
    self.debug     = False # debug mode (also use python -u for unbuffered printing)
    # Parse JSON descriptor
    with open(desc, 'r') as descriptor:
      self.desc_dict = json.loads( descriptor.read() )
    # Helpers
    self.inputs     = self.desc_dict['inputs'] # Structure: [ {id:...},...,{id:...} ]
    self.groups     = self.desc_dict['groups'] if 'groups' in self.desc_dict.keys() else []
    self.byId       = lambda n: [ v for v in self.inputs if v['id']==n][0]
    self.byGid      = lambda g: [ v for v in self.groups if v['id']==g][0]
    self.safeGet    = lambda i,k: None if not k in self.byId(i).keys() else self.byId(i)[k]
    self.safeGrpGet = lambda g,k: None if not k in self.byGid(g).keys() else self.byGid(g)[k]
    self.assocGrp   = lambda i: (filter( lambda g: i in g["members"], self.groups ) or [None])[0]
    self.reqsOf     = lambda t: self.safeGet(t,"requires-inputs") or []

  # Attempt execution
  def execute(self):
    command = self.cmdLine[0]
    print('Attempting execution of command:\n\t' + command + '\n---/* Start program output */---')
    # Run command
    try:
      # Note: invokes the command through the shell (potential injection dangers)
      process = subprocess.Popen( command , shell=True )
    except OSError as e:
      sys.stderr.write( 'OS Error during attempted execution!' )
      raise e
    except ValueError as e:
      sys.stderr.write( 'Input Value Error during attempted execution!' )
      raise e
    else:
      exit_code = process.wait()
      # Report exit status
      print('---/* End program output */---\nCompleted execution (exit code: ' + str(exit_code) + ')')
      time.sleep(0.5) # Give the OS a (half) second to finish writing
      # Check for output files (note: the path-template can contain command-line-keys
      print('Looking for output files:')
      for outfile in self.desc_dict['output-files']:
        # Generate correct path template based on input arguments
        template = outfile['path-template']
        for (kid,key) in [(q['id'],q['command-line-key']) for q in self.inputs]:
          # Blanks are entered if template key is not present
          # Note: may wish to detect output files whose paths depend on particular inputs
          # and not search for them if the key is not present
          val = '' if not (kid in self.in_dict.keys()) else self.in_dict[kid]
          template = template.replace(key,val)
        # Look for the target file
        exists = os.path.exists( template )
        # Note whether it could be found or not
        isOptional = outfile['optional'] if 'optional' in outfile.keys() else False
        s1 = 'Optional' if isOptional else 'Required'
        s2 = '' if exists else 'not'
        print("\t"+s1+" output file \'"+outfile['name']+"\' was "+s2+" found at "+template)

  # Generates a random input parameter set that follows the given constraints
  def _randomFillInDict(self):
    # Helpers for generating random numbers, strings, etc...
    nd, nl   = 3, 5 # Number of random chars to add to things, or max list items to have
    randDigs = lambda: ''.join(rnd.choice(string.digits) for _ in range(nd))
    randFile = lambda: 'f_' + randDigs() + rnd.choice(['.csv','.tex','.mnc','.cpp','.m','.mnc','.nii.gz'])
    randStr  = lambda: 'str_' + ''.join(rnd.choice(string.digits+string.ascii_letters) for _ in range(nd))
    def randNum(p): # generate random number that satisfies the param constraints
      i, defaultMin, defaultMax = p['id'], -50, 50
      isInt = self.safeGet( i , 'integer' )
      roundTowardsZero = lambda x: int(math.copysign(1,x)*int(abs(x)))
      # Assign random values to min and max, unless they have been specified
      minv, maxv = self.safeGet( i , 'minimum' ), self.safeGet( i , 'maximum' )
      if minv is None and maxv is None: minv, maxv = defaultMin, defaultMax
      elif minv is None and not (maxv is None): minv = maxv + defaultMin
      elif not (minv is None) and maxv is None: maxv = minv + defaultMax
      # Coerce the min/max to the proper number type
      if isInt: minv, maxv = roundTowardsZero(minv), roundTowardsZero(maxv)
      else: minv, maxv = float(minv), float(maxv)
      # Apply exclusive boundaries if any
      if self.safeGet( i , 'exclusive-minimum' ): minv += (1 if isInt else 0.0001)
      if self.safeGet( i , 'exclusive-maximum' ): maxv -= (1 if isInt else 0.0001)
      return (rnd.randint(minv,maxv) if isInt else round(rnd.uniform(minv,maxv),nd) )
    def paramSingle(prm): # generate a random parameter value based on the input type
      if prm['type']=='Enum':   return rnd.choice( self.safeGet(prm['id'],'enum-value-choices') )
      if prm['type']=='File':   return randFile()
      if prm['type']=='String': return randStr()
      if prm['type']=='Number': return randNum(prm)
      if prm['type']=='Flag':   return rnd.choice(['true','false'])
    def makeParam(prm): # generate random single or list params based on inputs
      mn = self.safeGet(prm['id'], 'min-list-entries') or 2
      mx = self.safeGet(prm['id'], 'max-list-entries') or nl
      isList = self.safeGet(prm['id'], 'list') or False
      return ' '.join(str(paramSingle(prm)) for _ in range(rnd.randint(mn,mx))) if isList else paramSingle(prm)
    def disablersOf(tid): # Returns a list of the ids of parameters that disable the input parameter
      return map(lambda p: p[0], # p[0] is the id
             filter(lambda t: tid['id'] in t[1], # t[1] is the disables list
             map(lambda p: (p['id'], self.safeGet(p['id'],'disables-inputs') or []), self.inputs) ))
    def mutReqs( targ ): # Returns the list of mutually requiring parameters of the target
      return map(lambda x: self.byId(x[0]),
             filter(lambda a: targ['id'] in a[1],
             map(lambda r: (r,self.reqsOf(r)), self.reqsOf(targ['id']) ) ) )
    def isOrCanBeFilled( targ ): # Returns whether targ has a value or is allowed to have one
      # If it is already filled in
      if targ['id'] in self.in_dict.keys(): return True
      # If a disabler or a disabled target is already active
      for d in disablersOf( targ ) + (self.safeGet( targ['id'], 'disables-inputs' ) or []):
        if d in self.in_dict.keys(): return False
      # If at least one non-mutual requirement has not been met
      for r in self.reqsOf(targ['id']):
        if not r in self.in_dict: # If a requirement is not present
          if not targ['id'] in self.reqsOf(r): # and it is not mutually required
            return False
      # If it is in a mutex group with one target already chosen
      g = self.assocGrp( targ['id'] )
      if (not g is None) and self.safeGrpGet(g['id'],'mutually-exclusive'):
        if len(filter(lambda x: x in self.in_dict.keys(), g['members'])) > 0: return False
      return True
    # Handle the mutual requirement case by BFS in the (implicitly defined) requirement graph
    # Returns False if at least one of the mutual requirements cannot be met
    # Returns a list of params to fill in if all of them can be met (or [targ.id] if it has no mutReqs)
    def checkMutualRequirements(targ):
      checked, toCheck = [], [targ]
      while len(toCheck) > 0:
        current = toCheck.pop()
        checked.append( current )
        if not isOrCanBeFilled( current ): return False
        for mutreq in mutReqs( current ):
          if not mutreq['id'] in [c['id'] for c in checked]: toCheck.append(mutreq)
      return checked
    # Clear the dictionary
    self.in_dict = {}
    # Fill in the required parameters
    for reqp in [r for r in self.inputs if self.safeGet(r['id'],'optional')==False]:
      self.in_dict[reqp['id']] = makeParam(reqp)
    # Fill in a random choice for each one-is-required group
    for grp in [g for g in self.groups if self.safeGrpGet(g['id'],'one-is-required')]:
      while True: # Loop to choose an allowed value, in case a previous choice disabled that one
        choice = self.byId( rnd.choice( grp['members'] ) )
        res = checkMutualRequirements( choice )
        if res==False: continue # Try again if the chosen group member is not permissable
        for r in res: self.in_dict[r['id']] = makeParam(r)
        break
    # Choose a random number of times to try to fill optional inputs
    opts = [p for p in self.inputs if self.safeGet(p['id'],'') in [None,True]]
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

  # Generate random parameter values
  def generateRandomParams(self,n):
    self.cmdLine = []
    for i in range(0,n):
      # Set in_dict with random values
      self._randomFillInDict()
      # Add the new command line
      if self.debug: print( "Input: " + str( self.in_dict ) )
      # Check results (as much as possible)
      try:
        self._validateDict()
      # If an error occurs, print out the problems already encountered before blowing up
      except Exception: # Avoid catching BaseExceptions like SystemExit
        sys.stderr.write("An error occurred in validation\nPreviously saved issues\n")
        for err in self.errs: sys.stderr.write("\t" + str(err) + "\n")
        raise
      self.cmdLine.append( self._generateCmdLineFromInDict() )

  # Read in parameter input file
  def readInput(self,infile):
    assert self.desc_dict != None
    # Read in input file (in_dict : id -> given value)
    with open(infile, 'r') as inparams:
      if infile.endswith('.csv'): # csv case
        lines = [ line.strip().split(",") for line in inparams.readlines() ]
        self.in_dict = { k.strip() : v.strip() for (k,v) in lines }
      else: # json case
        ins = json.loads( inparams.read() )['inputs']
        self.in_dict = { d.keys()[0] : d.values()[0] for d in ins }
    # Input dictionary
    if self.debug: print( "Input: " + str( self.in_dict ) )
    # Check results (as much as possible)
    try:
      self._validateDict()
    except Exception: # Avoid catching BaseExceptions like SystemExit
      sys.stderr.write("An error occurred in validation\nPreviously saved issues\n")
      for err in self.errs: sys.stderr.write("\t" + str(err) + "\n")
      raise
    # Build and save output command line (as a single-entry list)
    self.cmdLine = [ self._generateCmdLineFromInDict() ]

  # Build the actual command line by substitution, using the input data
  def _generateCmdLineFromInDict(self):
    # Get the command line template
    template = self.desc_dict['command-line']
    # Substitute every given value into the template (incl. flags, flag-seps, ...)
    for i in map(lambda x: x['id'], self.inputs):
      clk = self.safeGet(i,'command-line-key')
      assert not clk is None, str(i) + ' does not appear to have a command-line-key'
      # Substitute into the template if a value was given
      if i in self.in_dict.keys():
        # Generate value to put in template
        flag   = self.safeGet(i,'command-line-flag') or ''
        sep    = self.safeGet(i,'command-line-flag-separator') or ' '
        inval  = self.in_dict[i]
        outval = flag + sep + str(inval)
        if self.safeGet(i,'type')=='Flag': # special case for flag-type inputs
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

  # Validate input params
  def _validateDict(self):
    # Holder for errors
    self.errs = []
    # Check individual inputs
    for key in self.in_dict:
      isList = self.safeGet(key,"list")
      # Get current value and schema descriptor properties
      val, targ = self.in_dict[key], self.byId( key )
      # Helper functions
      def isNumber(s,intCheck = False):
        try: int(s) if intCheck else float(s); return True
        except ValueError: return False
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
        # Should be 'true' or 'false' when lower-cased
        check(None, lambda x,y: x.lower() in ["true","false"], "is not a valid flag value",val)
      # List length constraints are satisfied
      if isList: check('min-list-entries', lambda x,y: len(x.split()) >= targ[y], "violates min size",val)
      if isList: check('max-list-entries', lambda x,y: len(x.split()) <= targ[y], "violates max size",val)
    # Required inputs are present
    for reqId in [v['id'] for v in self.inputs if v['optional']==False]:
      if not reqId in self.in_dict.keys():
        self.errs.append('Required input ' + str(reqId) + ' is not present')
    # Disables/requires is satisfied
    for givenVal in [v for v in self.inputs if v['id'] in self.in_dict.keys()]:
      for r in self.reqsOf(givenVal['id']):
        if not r in self.in_dict.keys():
          self.errs.append('Input '+str(givenVal['id'])+' is missing requirement '+str(r))
      for d in (givenVal['disables-inputs'] if 'disables-inputs' in givenVal.keys() else []):
        if d in self.in_dict.keys():
          self.errs.append('Input '+str(d)+' should be disabled by '+str(givenVal['id']))
    # Group one-is-required/mutex is ok
    for group,mbs in map(lambda x: (x,x["members"]),self.groups):
      if ("mutually-exclusive" in group.keys()) and group["mutually-exclusive"]:
        if len(set.intersection( set(mbs) , set(self.in_dict.keys()) )) > 1:
          self.errs.append('Group ' + str(group["id"]) + ' is supposed to be mutex')
      if ("one-is-required" in group.keys()) and group["one-is-required"]:
        if len(set.intersection( set(mbs) , set(self.in_dict.keys()) )) < 1:
          self.errs.append('Group ' + str(group["id"]) + ' requires one member to be present')
    # Fast-fail if there was a problem
    if len(self.errs) != 0:
      sys.stderr.write("Problems found with prospective input:\n")
      for err in self.errs: sys.stderr.write("\t" + err + "\n")
      sys.exit(1)

# Execute program
if  __name__ == "__main__":

  # Parse arguments
  parser = argparse.ArgumentParser(description = 'Local tool executor to test JSON descriptors for the Boutiques framework')
  parser.add_argument('desc', metavar='descriptor', nargs = 1, help = 'The input JSON tool descriptor to test.')
  parser.add_argument('-i', '--input', help = 'Input parameter values with which to test the generation (.json or .csv).')
  parser.add_argument('-e', '--execute', action = 'store_true', help = 'Execute the program with the given inputs.  Requires -i.')
  parser.add_argument('-r', '--random', action = 'store_true', help = 'Generate a random set of input parameters to check.')
  parser.add_argument('-n', '--num', type = int, help = 'Number of random parameter sets to examine')
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
  elif args.execute and not given(args.input):
    errExit('--exec requires --input be specified')
  elif not os.path.isfile( desc ):
    errExit('The input JSON descriptor does not seem to exist', False)
  elif not args.random and not given(args.input):
    errExit('The default mode requires an input (-i)')
  elif not given(args.num):
    args.num = 1

  # Generate object that will perform the commands
  executor = LocalExecutor(desc)

  ### Run the executor with the given parameters ###
  # Execution case
  if args.execute:
    # Read in given input
    executor.readInput(args.input)
    # Execute it
    executor.execute()
  # Print random case
  elif args.random:
    # Generate random input
    executor.generateRandomParams(args.num)
    # Print the resulting command line
    executor.printCmdLine()
  # Print input case
  else:
    # Read in given input
    executor.readInput(args.input)
    # Print the resulting command line
    executor.printCmdLine()

