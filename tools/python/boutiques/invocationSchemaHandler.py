#!/usr/bin/env python

# A script for handling invocation schema generation and validation for Boutiques application descriptors
# Requires jsonschema 2.5

import json
import jsonschema as jsa
import os
import sys
import argparse
from functools import reduce
from boutiques.validator import validate_json

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
    "description"          : "Invocation schema for " + str(descName.lower()) + ".",
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
      elif i['value-choices']: return { 'enum' : i['value-choices'] }
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
  reqInputs = [x['id'] for x in [x for x in inputs if not x.get('optional')]]
  if len(list(reqInputs)) > 0: schema["required"] = reqInputs
  # Helper functions (assumes properly formed descriptor)
  byInd  = lambda id: [i for i in inputs if id==i['id']][0]
  isFlag = lambda id: (byInd(id)['type'] == 'Flag')
  # Handle one-is-required groups
  g1r = [g for g in groups if g.get("one-is-required")]
  def reqMember(m): # Generate code for a one-is-required member
    if isFlag(m): return { "properties" : { m : { "enum" : [ True ] } }, "required" : [m] }
    else: return { "required" : [m] }
  if len(g1r) > 0: schema["allOf"] = [{"anyOf" : list(map(reqMember, g['members']))} for g in g1r]
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
    errExit("Invocation schema is invalid.\n" + str(se.message), False)
  # Check data instance against schema
  if d:
    try:
      jsa.validate(d, s)
    except jsa.ValidationError as e:
      print(str(e))
      raise jsa.ValidationError(e)
    print("Invocation Schema validation OK")
          
# Script exit helper
def errExit(msg, parser, err_code = 1):
    sys.stderr.write('Error: ' + msg + '\n')
    sys.exit( err_code )

def main(args=None):

  # Description
  description = "Adds an invocation schema to a Boutiques descriptor. If an invocation is passed, validates it against invocation schema."
  # Parse inputs
  parser = argparse.ArgumentParser(description = description, formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('tool',   help = 'Boutiques tool descriptor.')
  parser.add_argument('-i', '--invocation',    help = 'Input values in a JSON file to be validated against the invocation schema.')
  result = parser.parse_args() if args is None else parser.parse_args(args)
   
  # Read in JSON (fast fail if invalid)
  try:
    validate_json(result.tool) # validates boutiques descriptor
    if result.invocation:
      data = json.loads(open(result.invocation).read())
  except Exception as e:
    print(str(e))
    errExit("Error during JSON parsing: " + str( e.message ), parser)

  # Do the work
  desc = json.loads(open(result.tool).read())
  invSchema = desc.get('invocation-schema') if desc.get('invocation-schema') else generateInvocationSchema(desc)
  desc['invocation-schema'] = invSchema
  with open(result.tool,'w') as f:
    f.write(json.dumps(desc, indent=4, sort_keys=True))
  if result.invocation:
    validateSchema(invSchema, data)

# Main program start
if __name__ == "__main__":
    main()

