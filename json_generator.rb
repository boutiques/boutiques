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
$:.unshift "lib-ruby/"
require 'colorize'
require 'tool_input_output'
require 'tool_input'
require 'tool_output'
require 'tool_templates'
require 'tool_descriptor'
require 'tool_creator'

def get_input i
  puts "> Input ##{i}".green
  name = get_param " >> Input name:"
  description = get_param " >> Input description:",true
  type = get_param " >> Input type:",false,"File",["String","File","Flag"]
  key = get_param " >> Input command-line key",true
  cardinality = type == "Flag" ? "Single" : get_param(" >> Input cardinality",false,"Single",["Single","Multiple"])
  optional = type == "Flag" ? "True" : get_param(" >> Is input optional?",false,"False",["True","False"])
  command_line_flag = get_param " >> Command-line flag:",true
  return ToolInput.new name,type,key,description,cardinality,optional,command_line_flag
end

def get_output i
  puts "> Output ##{i}".green
  name = get_param " >> Output name:"
  description = get_param " >> Output description:",true
  type = get_param " >> Output type:",false,"File",["File"]
  key = get_param " >> Output command-line key",true
  cardinality = get_param " >> Output cardinality",false,"Single",["Single","Multiple"]
  optional = get_param " >> Is output optional?",false,"False",["True","False"]
  command_line_flag = get_param " >> Command-line flag:",true
  must_be_contained = cardinality == "Multiple" ? "*" : nil
  template = get_param " >> Output value template",false,nil,nil,must_be_contained
  return ToolOutput.new name,type,key,template,description,cardinality,optional,command_line_flag
end

def get_param message,can_be_empty=false,default_value=nil,accepted_values=nil,must_be_contained=nil
  _message = default_value ? message+" (default: #{default_value})" : message
  if accepted_values
    values ="(accepted values: "
    accepted_values.each_with_index do |x,index|
      values += " " unless index == 0 
      values += "\"#{x}\""
    end
    values +=")"
    _message += " #{values}"
  end
  _message += " (value must contain: \"#{must_be_contained}\")" if must_be_contained
  
  puts _message.blue
  param = gets.chomp.strip
  if param != ""
    # check if value is acceptable
    return param if ( ( not accepted_values ) or accepted_values.include? param ) and ( not must_be_contained or param.include? must_be_contained )
    puts "Wrong value!".red
    return get_param message,can_be_empty,default_value,accepted_values,must_be_contained
  else
    return default_value if default_value
    return nil if can_be_empty
    puts "Please provide a value!".red
    get_param message,can_be_empty,default_value,accepted_values
  end
  # not reachable
end

################
# Main program #
################

# Fixed parameters
default_docker_index = "http://index.docker.io"
schema_version      = "0.2-snapshot"

# get parameters
name                 = get_param "> Tool name:"
description          = get_param "> Tool description:",true
syntax               = get_param "> Tool syntax:"
docker_image         = get_param "> Docker image name:"
docker_index         = get_param "> Docker index:",false,default_docker_index

# inputs 
inputs = Array.new 
#puts "> Tool input ##{inputs.length+1}"
continue = "Y"
while continue.downcase.strip.start_with? "y" do
  inputs << get_input(inputs.length)
  continue = get_param "> Add another input?",false,"Y"
end


# outputs 
outputs = Array.new
continue = "Y"
while continue.downcase.strip.start_with? "y" do
  outputs << get_output(outputs.length)
  continue = get_param "> Add another output?",false,"Y"
end

# output file name
output_file_name = nil
while not output_file_name do
  output_file_name = get_param "> Output file where to write the JSON descriptor:",false,"#{name}.json",nil,nil
  if File.exist? output_file_name
    overwrite = get_param "> File #{output_file_name} exists, overwrite?",false,"N"
    output_file_name = overwrite.downcase == "y" ? output_file_name : nil 
  end
end

tool_descriptor = ToolDescriptor.new
tool_descriptor.create_from_params name,description,syntax,inputs,outputs,docker_image,docker_index,schema_version

File.open(output_file_name, 'w') { |file| file.write(tool_descriptor.to_json) }

puts "Bye!".green
