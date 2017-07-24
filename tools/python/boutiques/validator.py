#!/usr/bin/env python
#
# Copyright (C) 2015
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
import simplejson
import os.path as op
from jsonschema import validate, ValidationError
from argparse import ArgumentParser
from boutiques import __file__

# Defining helper functions/lambdas
def safeGet(sec, targ):
    values = []
    for item in descriptor[sec]:
        try:
            values += [item[targ]]
        except KeyError:
            continue
    return values

inputGet  = lambda s: safeGet('inputs', s)
outputGet = lambda s: safeGet('output-files', s)
groupGet  = lambda s: safeGet('groups', s)
inById    = lambda i: descriptor['inputs'][inputGet('id').index(i)] if i in inputGet('id') else {}

# Main validation module
def validate_json(json_file):
    """
    Validates the Boutiques descriptor against the schema.
    """
    path, fil = op.split(__file__)
    schema_file = op.join(path, 'schema', 'descriptor.schema.json')

    # Load schema
    with open(schema_file) as fhandle:
        schema = simplejson.load(fhandle)

    # Load descriptor
    with open(json_file) as fhandle:
        descriptor = simplejson.load(fhandle)

    # Validate basic JSON schema compliance for descriptor
    # Note: if it fails basic schema compliance we don't do more checks
    try:
        validate(descriptor, schema)
    except ValidationError as e:
        print("Descriptor is not compliant with Boutiques schema.")
        print("Error: {}".format(e.strerror))
        return -1

    # Begin looking at Boutiques-specific failures
    errors = []
    
    # Verify that all command-line key appear in the command-line
    clkeys = inputGet('value-key') + outputGet('value-key')
    configFileTemplates = outputGet('file-template') + outputGet('path-template')
    cmdline = descriptor['command-line']

    msg_template = "{} not in command-line or file template"
    errors += [msg_template.format(k) for k in clkeys
               if (cmdline.count(k) + " ".join(configFileTemplates).count(k)) < 1 ]

    """
    # Command-line keys are not contained within each other
    clkeys.each_with_index do |key1,i|
      for j in 0...(clkeys.length)
        errors.push( key1 + ' contains ' + clkeys[j] ) if key1.include?(clkeys[j]) && i!=j
      end
    end
    """

def main():
    parser = ArgumentParser("Boutiques Validator")
    parser.add_argument("json_file", action="store", nargs="1",
                        help="The Boutiques descriptor you wish to validate")
    json_file = parser.parse_args()['json_file']
    validate_json(json_file)


if __name__ == "__main__":
    main()

thing = """
# Every command-line key appears in the command line
clkeys  = inputGet.( 'value-key' ) + outputGet.( 'value-key' )
configFileTemplates = outputGet.( 'file-template' )
cmdline = descriptor[ 'command-line' ]
clkeys.each { |k| errors.push( k + ' not in cmd line or file template' ) unless (cmdline.include?(k) || configFileTemplates.join(" ").include?(k))}

# Command-line keys are not contained within each other
clkeys.each_with_index do |key1,i|
  for j in 0...(clkeys.length)
    errors.push( key1 + ' contains ' + clkeys[j] ) if key1.include?(clkeys[j]) && i!=j
  end
end

# IDs are unique
inIds, outIds, grpIds = inputGet.( 'id' ), outputGet.( 'id' ), groupGet.( 'id' )
allIds = inIds + outIds + grpIds
allIds.each_with_index do |s1,i|
  allIds.each_with_index do |s2,j|
    errors.push("Non-unique id " + s1) if (s1 == s2) && (i < j)
  end
end

## Checking outputs ##
descriptor['output-files'].each_with_index do |a,i|

  # Output files should have a unique path-template
  descriptor['output-files'].each_with_index do |b,j|
    next if j <= i
    if a['path-template'] == b['path-template']
      errors.push( "Output files #{a['id']} and #{b['id']} have the same path-template" )
    end
  end

end

## Checking inputs ##
descriptor["inputs"].each do |v|

  # Flag-type inputs always have command-line-flags, should not be required, and cannot be lists
  if v["type"] == "Flag"
    errors.push( "#{v["id"]} must have a command-line flag" ) unless v["command-line-flag"]
    errors.push( "#{v["id"]} cannot be a list" ) if v["list"]
    errors.push( "#{v["id"]} should not be required" ) if v["optional"]==false
  # Number constraints (mins & maxs) are sensible
  elsif v["type"] == "Number"
    min, max = v["minimum"] || -1.0/0, v["maximum"] || 1.0/0
    errors.push( "#{v['id']} cannot have greater min (#{min}) than max (#{max})" ) if min > max
  # Enum-type inputs always have specified choices (at least 1), and the default must be in the choices set
  elsif v["value-choices"]
    errors.push( "#{v['id']} must have at least one value choice" ) if (v["value-choices"] || []).length < 1
    badDefault = (ed = v["default-value"]).nil? ? false : !((v["value-choices"] || []).include? ed)
    errors.push( "#{v['id']} cannot have an default value outside its choices" ) if badDefault
  end

  # List length constraints are sensible
  if v["list"]
    min, max = v["min-list-entries"] || 0, v["max-list-entries"] || 1.0 / 0
    errors.push( "#{v['id']} min list entries (#{min}) greater than max list entries (#{max})" ) if min > max
    errors.push( "#{v['id']} cannot have negative min list entries #{min}" ) if min < 0
    errors.push( "#{v['id']} cannot have non-positive max list entries #{max}" ) if max <= 0
  # Non-list inputs cannot have the min/max-list-entries property
  else
    ['min','max'].each{ |r| errors.push("#{v['id']} can't use #{r}-list-entries") if v["#{r}-list-entries"] }
  end

  # IDs in requires-inputs and disables-inputs are present
  for s in ['require','disable']
    (v[s + "s-inputs"] || []).each do |r|
      errors.push( s.capitalize + "d id #{r} for #{v['id']} was not found" ) unless inIds.include?(r)
    end
  end

  # An input cannot both require and disable another input
  for did in (v["requires-inputs"] || [])
    errors.push( "Id #{v['id']} requires and disables #{did}" ) if (v["disables-inputs"] || []).include?(did)
  end

  # Required inputs cannot require or disable other parameters
  if v['optional']==false
     errors.push("Required param #{v['id']} cannot require other inputs") if v['requires-inputs']
     errors.push("Required param #{v['id']} cannot disable other inputs") if v['disables-inputs']
  end

end

## Checking Groups ##
(descriptor["groups"] || []).each_with_index do |g,gi|

  # Group members must exist in the inputs, but cannot appear multiple times (in the same group or across groups)
  g['members'].each_with_index do |mcurr,i|
    (descriptor["groups"] || []).each_with_index do |g2,gj|
      g2['members'].each_with_index do |moth,j|
        unless gi > gj || (gi == gj && i >= j) # Prevent seeing the same error twice
          errors.push( "#{mcurr} cannot appear twice (in groups #{g["id"]} & #{g2["id"]})" ) if mcurr == moth
        end
      end
    end
    errors.push("Member id #{mcurr} from group #{g['id']} is not present in the inputs") unless inIds.include?(mcurr)
  end

  # Mutually exclusive groups cannot have members requiring other members, nor can they have required members
  if g["mutually-exclusive"]
    (mbrs = g["members"]).map{ |m| [m,inById.(m)] }.each do |id,m|
      errors.push( "#{id} in mutex group #{g['id']} cannot be required" ) unless m['optional'] != false
      for r in (m["requires-inputs"] || [])
        errors.push( "#{id} in mutex group #{g['id']} cannot require fellow member " + r ) if mbrs.include?( r )
      end
    end
  end

  # One-is-Required groups should also never have required members (since it is automatically satisfied)
  if g["one-is-required"]
    g["members"].map{ |m| [m,inById.(m)] }.each do |id,m|
      errors.push( "#{id} in one-is-required group #{g['id']} should not be required" ) unless m['optional'] != false
    end
  end

end

### Print the final set of errors ###
errors << "OK" if errors == []
puts "#{errors}"
"""
