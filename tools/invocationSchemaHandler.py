#!/usr/bin/env python

# A script for handling invocation schema generation and validation for Boutiques application descriptors
# Requires jsonschema 2.5

import json, jsonschema as jsa, argparse, os, sys

# Generate an invocation schema from a Boutiques application descriptor
def generateInvocationSchema(toolDesc, oname=None, validateWrtMetaSchema=True):
  # Subclass dictionary to act more like a ruby hash map
  class RMap(dict):
    def __getitem__(self, key): return dict.get(self, key)
  s = RMap(toolDesc)
  descName, inputs, groups = s['name'], s['inputs'], s['groups'] or []
  oname = descName + ".invocationSchema" if oname is None else oname
  schema = {
    "$schema"              : "http://json-schema.org/draft-04/schema#",
    "title"                : str(oname),
    "description"          : "Input parameters schema for " + str(descName.lower()) + ".",
    "type"                 : "object",
    "additionalProperties" : False
  }
  if inputs is None: return schema
  # Handle type constraints for single inputs
  def addTypeConstraints(h,ind):
    i = RMap( ind )
    id, type, target = i['id'], i['type'], None
    def undertype():
      if i['integer']: return { 'type' : 'integer' }
      elif type == "Enum": return { 'enum' : i['enum-value-choices'] }
      elif type == "File": return { 'type' : 'string' }
      elif type == "Flag": return { 'type' : 'boolean' }
      else: return { 'type' : type.lower() }
    if i['list']:
      h[id] = { 'type'  : 'array', 'items' : undertype() }
      if i["min-list-entries"]: h[id]["minItems"] = i["min-list-entries"]
      if i["max-list-entries"]: h[id]["maxItems"] = i["max-list-entries"]
      target = h[id]["items"]
    else:
      h[id] = undertype()
      target = h[id]
    if not i["minimum"] is None: target["minimum"] = i["minimum"] # Python treats 0 as false
    if not i["maximum"] is None: target["maximum"] = i["maximum"]
    if i["exclusive-minimum"]: target["exclusiveMinimum"] = i["exclusive-minimum"]
    if i["exclusive-maximum"]: target["exclusiveMaximum"] = i["exclusive-maximum"]
    return h
  schema["properties"] = reduce(addTypeConstraints, inputs, {})
  # Required inputs
  reqInputs = map(lambda x: x['id'], filter(lambda x: not x.get('optional'), inputs))
  if len(reqInputs) > 0: schema["required"] = reqInputs
  # Helper functions (assumes properly formed descriptor)
  byInd  = lambda id: [i for i in inputs if id==i['id']][0]
  isFlag = lambda id: (byInd(id)['type'] == 'Flag')
  # Handle one-is-required groups
  g1r = [g for g in groups if g.get("one-is-required")]
  def reqMember(m): # Generate code for a one-is-required member
    if isFlag(m): return { "properties" : { m : { "enum" : [ True ] } }, "required" : [m] }
    else: return { "required" : [m] }
  if len(g1r) > 0: schema["allOf"] = map(lambda g: {"anyOf" : map(reqMember, g['members'])}, g1r)
  # Handle requires and disables-inputs/mutex constraints
  def handleDisablesRequires(h,inval):
    i, h = RMap( inval ), RMap( h )
    id, reqs, disbs = i['id'], i['requires-inputs'], i['disables-inputs'] or []
    # Mutex group members added to disablees list
    for g in [g for g in groups if g.get('mutually-exclusive') and (id in g['members'])]:
      for m in [m for m in g['members'] if not m==id]: disbs.append( m )
    # Handle requires-inputs (flags have to be true to satisfy it)
    if reqs:
      reqMap = { r : { "enum" : [ True ] } for r in reqs if isFlag(r) }
      if isFlag( id ):
        h[id] = {}
        h[id]['anyOf'] = [
          { "properties" : reqMap, "required" : reqs },
          { "properties" : { id : { "enum" : [ False ] } } }
        ]
      else:
        h[id] = { "required" : reqs }
        h[id]['properties'] = reqMap
    # Handle disables-inputs (false flags do not violate the disabled criteria)
    if len(disbs) > 0:
      if h[id] is None: h[id] = RMap( {} )
      def makeSingleDisablesMap(dh, d): # Flags can be non-present or false
        if isFlag( d ): dh[d] = { "oneOf" : [ { "not" : {} }, { "enum" : [ False ] } ] }
        else: dh[d] = { "not" : {} }
        return dh
      disbMap = reduce(makeSingleDisablesMap, disbs, {})
      if isFlag( id ): # Flags do not disable their targets when false
        if h[id].get('anyOf') is None:
          h[id]['anyOf'] = [
            { "properties" : disbMap },
            { "properties" : { id : { "enum" : [ False ] } } }
          ]
        else: # Need to add disables properties to requires ones, if the latter exist
          h[id]['anyOf'][0]['properties'].update( disbMap )
      else:
        if h[id].get('properties') is None: h[id]['properties'] = RMap( {} )
        h[id]['properties'].update( disbMap )
    return h
  schema["dependencies"] = reduce(handleDisablesRequires, inputs, {})
  # Validate wrt meta-schema if desired
  if validateWrtMetaSchema: validateSchema( schema )
  # Return final schema
  return schema

# Validate data with respect to the invocation schema
def validateSchema(s, d=None):
  # Check schema wrt meta-schema
  try:
    jsa.Draft4Validator.check_schema(s)
  except jsa.SchemaError as se:
    errExit("Invocation schema is invalid wrt meta-schema!\n" + str(se.message), False)
  # Check data instance against schema
  if not d is None:
    errs  = list(jsa.Draft4Validator(s).iter_errors(d))
    nerrs = len( errs )
    if nerrs > 0:
      print("Encountered " + str(nerrs) + " error" + ('s!' if nerrs > 1 else '!') )
      for e in sorted(errs, key=str): print("\t" + str(e.message))
      sys.exit(1)
    else:
      print("Valid data!")
      sys.exit(0)

# Write an invocation schema out
def writeSchema(s, f, indenter=3):
  with open(f,"w") as outfile: outfile.write( _prettySchema( s, indenter ) )

# Script exit helper
def errExit(msg, print_usage = True, err_code = 1):
    if print_usage: parser.print_usage()
    sys.stderr.write('Error: ' + msg + '\n')
    sys.exit( err_code )

# Pretty version of a schema
def _prettySchema(s, indenter=3): return json.dumps( s, indent=indenter, separators=(',', ' : ') )

# Main program start
if __name__ == "__main__":

  # Description
  description = "\n".join(map(lambda x: x[3:],'''
   Script for generating invocation schemas (i.e. JSON schemas for input values) associated to a Boutiques application
     descriptor and/or validating input data examples with respect to invocation schemas.

   Example usages:
     Generate input schema (printed to console)
       python invocationSchemaHandler.py -i toolDescriptor.json
     Generate input schema (printed in compact form)
       python invocationSchemaHandler.py -i tooDescriptor.json -c
     Write input schema to output file
       python invocationSchemaHandler.py -i toolDescriptor.json -o tool.invocationSchema.json
     Validate input data (i.e. tool parameter arguments) with implicit invocation schema generation
       python invocationSchemaHandler.py -i toolDescriptor.json -d tool.exampleInputs.json
     Validate input with respect to invokation schema (standard json schema validation)
       python invocationSchemaHandler.py -s tool.invocationSchema.json -d tool.exampleInputs.json

   Example input (i.e. that passed by -d) must be a single JSON data map, such as:
     {
        "inputFile" : "input.csv",
        "outputFile" : "output.gif",
        ...
     }
  '''.split("\n")))

  # Parse inputs
  parser = argparse.ArgumentParser(description = description, formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('-i', '--input',   help = 'Input Boutiques json tool or application descriptor')
  parser.add_argument('-o', '--output',  help = 'Output file to which a generated invokation schema is written')
  parser.add_argument('-d', '--data',    help = 'Input values in a json file, to be validated against the invocation schema')
  parser.add_argument('-s', '--schema',  help = 'An invocation schema json file')
  parser.add_argument('-c', '--compact', action = 'store_true', help = 'Compact printing')
  args = parser.parse_args()

  # Check arguments
  given = lambda x: not (x is None)
  if given(args.input) and given(args.schema):
    errExit('-i and -s cannot be used together')
  elif (not given(args.input)) and (not given(args.schema)):
    errExit('At least one of -i and -s is required')
  elif (not given(args.input)) and given(args.output):
    errExit('-o cannot be used without -i')
  elif given(args.output) and (given(args.data) or given(args.schema)):
    errExit('-o cannot be used with -d or -s')
  elif given(args.schema) and (not given(args.data)):
    errExit('-s cannot be used without -d')
  elif given(args.schema) and (given(args.input) or given(args.output)):
    errExit('-s cannot be used with -i or -o')
  elif given(args.input) and not os.path.isfile( args.input ):
    errExit('Cannot find input file ' + str( args.input ) )
  elif given(args.data) and not os.path.isfile( args.data ):
    errExit('Cannot find data file ' + str( args.data ) )
  elif given(args.schema) and not os.path.isfile( args.schema ):
    errExit('Cannot find schema file ' + str( args.schema ) )
  elif args.compact and (given(args.schema) or given(args.data)):
    errExit('Cannot use -c with -s or -d')

  # Read in JSON (fast fail if invalid)
  try:
    if given(args.input):  desc     = json.loads( open(args.input).read() )
    if given(args.schema): inSchema = json.loads( open(args.schema).read() )
    if given(args.data):   data     = json.loads( open(args.data).read() )
  except Exception as e:
    errExit("Error incurred during json parsing: " + str( e.message ))

  # Validate, write, or print depending on arguments
  invSchema = generateInvocationSchema(desc) if given(args.input) else inSchema
  if given(args.output): writeSchema(invSchema, args.output, None if args.compact else 3)
  elif given(args.data): validateSchema(invSchema, data)
  else: print(_prettySchema(invSchema, None if args.compact else 3))

