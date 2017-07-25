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
import numpy as np
from jsonschema import validate, ValidationError
from argparse import ArgumentParser
from boutiques import __file__


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
        print("JSON Validation error (Boutiques validation not yet performed)")
        print("Error: {}".format(e))
        return -1

    # Helper get-function
    safeGet   = lambda desc, sec, targ: [item[targ] for item in desc[sec]
                                         if list(item.keys()).count(targ)]
    inputGet  = lambda s: safeGet(descriptor, 'inputs', s)
    outputGet = lambda s: safeGet(descriptor, 'output-files', s)
    groupGet  = lambda s: safeGet(descriptor, 'groups', s)
    inById    = lambda i: descriptor['inputs'][inputGet('id').index(i)] if i in inputGet('id') else {}

    # Begin looking at Boutiques-specific failures
    errors = []
    
    clkeys = inputGet('value-key') + outputGet('value-key')
    configFileTemplates = outputGet('file-template') + outputGet('path-template')
    cmdline = descriptor['command-line']

    # Verify that all command-line key appear in the command-line
    msg_template = "   KeyError: \"{}\" not in command-line or file template"
    errors += [msg_template.format(k.strip("[]"))
               for k in clkeys
               if (cmdline.count(k) + " ".join(configFileTemplates).count(k)) < 1 ]

    # Verify that no key contains another key
    msg_template = "   KeyError: \"{}\" contains \"{}\""
    errors += [msg_template.format(key.strip("[]"), clkeys[jdx].strip("[]"))
               for idx, key in enumerate(clkeys)
               for jdx in range(0, len(clkeys))
               if clkeys[jdx].strip("[]") in key and key is not clkeys[jdx]]

    # Verify that all Ids are unique
    inIds, outIds, grpIds = inputGet('id'), outputGet('id'), groupGet('id')
    allIds = inIds + outIds + grpIds
    msg_template = "    IdError: \"{}\" is non-unique"
    for idx, s1 in enumerate(allIds):
        for jdx, s2 in enumerate(allIds):
            errors += [msg_template.format(s1)] if s1 == s2 and idx < jdx else []

    # Verify that output files have unique path-templates
    msg_template = "OutputError: \"{}\" and \"{}\" have the same path-template"
    for idx, out1 in enumerate(descriptor['output-files']):
        for jdx, out2 in enumerate(descriptor['output-files']):
            errors += [msg_template.format(out1['id'], out2['id'])] if out1['path-template'] == out2['path-template'] and jdx > idx else []

    # Verify inputs
    for inp in descriptor['inputs']:
    
        # Verify flag-type inputs (have flags, not required, cannot be lists)
        if inp['type'] == 'Flag':
            msg_template = " InputError: \"{}\" must have a command-line flag"
            errors += [msg_template.format(inp['id'])] if 'command-line-flag' not in inp.keys() else []

            msg_template = " InputError: \"{}\" should not be required"
            errors += [msg_template.format(inp['id'])] if inp['optional'] == False  else []

            # This one is redundant as basic JSON validation catches it
            msg_template = " InputError: \"{}\" cannot be a list"
            errors += [msg_template.format(inp['id'])] if 'list' in inp.keys() else []

        # Verify number-type inputs min/max are sensible
        elif inp['type'] == 'Number':
            msg_template = " InputError: \"{}\" cannot have greater min ({}) than max ({})"
            minn = inp['minimum'] if 'minimum' in inp.keys() else -np.inf 
            maxx = inp['maximum'] if 'maximum' in inp.keys() else np.inf
            errors += [msg_template.format(inp['id'], minn, maxx)] if minn > maxx else []

        # Verify enum-type inputs (at least 1 option, default in set)
        elif 'value-choices' in inp.keys():
            msg_template = " InputError: \"{}\" must have at least one value choice"
            errors += [msg_template.format(inp['id'])] if len(inp['value-choices']) < 1 else []

            msg_template = " InputError: \"{}\" cannot have default value outside its choices"
            errors += [msg_template.format(inp['id'])] if 'default-value' in inp.keys() and inp['default-value'] not in inp['value-choices'] else []

        # Verify list-type inputs (min entries less than max, no negative entries (both on min and max)
        if 'list' in inp.keys():
            msg_template = " InputError: \"{}\" cannot have greater min entries ({}) than max entries ({})"
            minn = inp['min-list-entries'] if 'min-list-entries' in inp.keys() else 0
            maxx = inp['max-list-entries'] if 'max-list-entries' in inp.keys() else np.inf
            errors += [msg_template.format(inp['id'], minn, maxx)] if minn > maxx else []

            msg_template = " InputError: \"{}\" cannot have negative min entries ({})"
            errors += [msg_template.format(inp['id'], minn)] if minn < 0 else []

            msg_template = " InputError: \"{}\" cannot have non-positive max entries ({})"
            errors += [msg_template.format(inp['id'], maxx)] if maxx <= 0 else []

        # Verify non list-type inputs don't have list properties
        # This one is redundant as basic JSON validation catches it
        else:
            msg_template = " InputError: \"{}\" cannot use min- or max-list-entries"
            errors += [msg_template.format(inp['id'])] if 'min-list-entries' in inp.keys() or 'max-list-entries' in inp.keys() else []

    errors = ["OK"] if errors == [] else errors
    print("\n".join(errors))
"""
## Checking inputs ##
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
puts "#{errors}"
"""
