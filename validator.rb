#!/usr/bin/ruby
#
# Copyright (C) 2015
# The Royal Institution for the Advancement of Learning
# McGill University
#    and
# Centre National de la Recherche Scientifique
# CNRS
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
#
require 'json-schema'

def usage
  puts "validate: [schema_file] [json_file]"
  exit
end

if ARGV.length != 2
  usage
end

# Unpack arguments and parse descriptor
(schema_file,json_file) = ARGV
begin
  descriptor = JSON.parse( File.read(json_file) )
rescue StandardError => e
  puts e # if json is invalid, no need to check it
  exit 1
end

### Automatic descriptor validation with respect to schema structure ###
errors = JSON::Validator.fully_validate(schema_file, descriptor)

### Validation of descriptor arguments ###

## Helper functions ##
inputGet  = lambda { |s| descriptor['inputs'].map {       |v| v[s] } }
outputGet = lambda { |s| descriptor['output-files'].map { |v| v[s] } }
groupGet  = lambda { |s| descriptor['groups'].map {       |v| v[s] } rescue [] }
inById    = lambda { |i| descriptor['inputs'].find{       |v| v['id']==i } || {} }

## Checking command-line-keys and IDs ##

# Every command-line key appears in the command line
clkeys, cmdline = inputGet.( 'command-line-key' ), descriptor[ 'command-line' ]
clkeys.each { |k| errors.push( k + ' not in cmd line' ) unless cmdline.include?(k) }

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

# IDs in groups, requires-inputs, and disables-inputs are present
(descriptor['groups'] || []).map{ |g| g['members'].map{ |m| [g['id'],m] } }.flatten(1).each do |gid,mid|
  errors.push("Member id #{mid} from group #{gid} is not present") unless inIds.include?(mid)
end
descriptor['inputs'].each do |d|
  for s in ['require','disable']
    (d[s + "s-inputs"] || []).each do |r|
      errors.push( s.capitalize + "d id #{r} for #{d['id']} was not found" ) unless inIds.include?(r)
    end
  end
end

# An input cannot both require and disable another input
descriptor["inputs"].each do |ins|
  for did in (ins["requires-inputs"] || [])
    errors.push( "Id #{ins['id']} requires and disables #{did}" ) if (ins["disables-inputs"] || []).include?(did)
  end
end

# Group members cannot appear multiple times (in the same group or across groups)
(descriptor["groups"] || []).each_with_index do |g1,gi|
  g1['members'].each_with_index do |mcurr,i|
    (descriptor["groups"] || []).each_with_index do |g2,gj|
      g2['members'].each_with_index do |moth,j|
        unless gi > gj || (gi == gj && i >= j) # Prevent seeing the same error twice
          errors.push( "#{mcurr} cannot appear twice (in groups #{g1["id"]} & #{g2["id"]})" ) if mcurr == moth
        end
      end
    end
  end
end

# Mutually exclusive groups cannot have members requiring other members, nor can they have required members
(descriptor["groups"] || []).select{ |g| g["mutually-exclusive"] }.each do |g|
  (mbrs = g["members"]).map{ |m| [m,inById.(m)] }.each do |id,m|
    errors.push( "#{id} in mutex group #{g['id']} cannot be required" ) unless m['optional'] != false
    for r in (m["requires-inputs"] || [])
      errors.push( "#{id} in mutex group #{g['id']} cannot require fellow member " + r ) if mbrs.include?( r )
    end
  end
end

# One-is-Required groups should also never have required members (since it is automatically satisfied)
(descriptor["groups"] || []).select{ |g| g["one-is-required"] }.each do |g|
  g["members"].map{ |m| [m,inById.(m)] }.each do |id,m|
    errors.push( "#{id} in one-is-required group #{g['id']} should not be required" ) unless m['optional'] != false
  end
end

# Flag-type inputs always have command-line-flags, should not be required, and cannot be lists
descriptor["inputs"].select{ |v| v["type"] == "Flag" }.each do |f|
  errors.push( "#{f["id"]} must have a command-line flag" ) unless f["command-line-flag"]
  errors.push( "#{f["id"]} cannot be a list" ) if f["list"]
  errors.push( "#{f["id"]} should not be required" ) if f["optional"]==false
end

# Number constraints (mins & maxs) are sensible
descriptor["inputs"].select{ |v| v["type"] == "Number" }.each do |f|
  min, max = f["minimum"] || -1.0/0, f["maximum"] || 1.0/0
  errors.push( "#{f['id']} cannot have greater min (#{min}) than max (#{max})" ) if min > max
end

# List length constraints are sensible
descriptor["inputs"].select{ |v| v["list"] }.each do |f|
  min, max = f["min-list-entries"] || 0, f["max-list-entries"] || 1.0 / 0
  errors.push( "#{f['id']} min list entries (#{min}) greater than max list entries (#{max})" ) if min > max
  errors.push( "#{f['id']} cannot have negative min list entries #{min}" ) if min < 0
  errors.push( "#{f['id']} cannot have non-positive max list entries #{max}" ) if max <= 0
end

# Enum-type inputs always have specified choices (at least 1), and the default must be in the choices set
descriptor["inputs"].select{ |v| v["type"] == "Enum" }.each do |e|
  errors.push( "#{e['id']} must have at least one value choice" ) if (e["enum-value-choices"] || []).length < 1
  badDefault = (ed = e["default-value"]).nil? ? false : !((e["enum-value-choices"] || []).include? ed)
  errors.push( "#{e['id']} cannot have an default value outside its choices" ) if badDefault
end

# Non-list inputs cannot have the min/max-list-entries property
descriptor["inputs"].each do |v|
  if v['list'] != true
    errors.push( "#{v['id']} cannot specify min-list-entries as a non-list" ) if v["min-list-entries"]
    errors.push( "#{v['id']} cannot specify max-list-entries as a non-list" ) if v["max-list-entries"]
  end
end

### Print the final set of errors ###
errors << "OK" if errors == []
puts "#{errors}"



























