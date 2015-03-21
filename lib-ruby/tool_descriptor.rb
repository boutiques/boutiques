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
require 'json'

# Class describing a Tool
class ToolDescriptor

  def initialize
  end
  
  def create_from_params name,description,syntax,inputs,outputs,docker_image,docker_index,schema_version
    @name = name                      # the  name of the Tool
    @description = description        # the description of the Tool
    @syntax = syntax                  # the syntax of the command line, containing placeholders for inputs and outputs
    @inputs = inputs                  # an array of ToolInput objects
    @outputs = outputs                # an array of ToolOutput objects
    @docker_image = docker_image      # a string describing the Docker image associated to this tool in DockerHub
    @docker_index = docker_index
    @schema_version = schema_version
  end

  def parse_from_json json_object
    # TODO json validation goes here
    hash = JSON.parse(json_object)
    @name = hash["name"]
    @description = hash["description"]
    @syntax = hash["command-line"]
    @docker_image = hash["docker-image"]
    @docker_index = hash["docker-index"]
    @schema_version = hash["schema-version"]
    @inputs = Array.new
    hash["inputs"].each do |input_hash|
      @inputs << ToolInput.new(input_hash["name"],input_hash["type"],input_hash["command-line-key"],input_hash["description"],input_hash["cardinality"])
    end
    @outputs = Array.new
    hash["outputs"].each do |output_hash|
      @outputs << ToolOutput.new(output_hash["name"],output_hash["type"],output_hash["command-line-key"],output_hash["value-template"],output_hash["description"],output_hash["cardinality"])
    end   
  end
  
  def get_name
    return @name
  end
  def get_description
    return @description
  end
  def get_syntax
    return @syntax
  end
  def get_inputs
    return @inputs
  end
  def get_outputs
    return @outputs
  end
  def get_docker_image
    return @docker_image
  end
  
  def get_binding
    binding()
  end

  def to_json
    json_string = "{ 
    \"name\" : \"#{@name}\",
    \"description\" : \"#{@description}\",
    \"command-line\" : \"#{@syntax}\",
    \"docker-image\" : \"#{@docker_image}\",
    \"docker-index\" : \"#{@docker_index}\",
    \"schema-version\" : \"#{@schema_version}\",
    \"inputs\" : [ 
    "  
    @inputs.each_with_index do |input,index|
      json_string += ",\n    " unless index == 0 
      json_string += input.to_json
    end
    json_string += "
    ],
    \"outputs\" : [
    "
    @outputs.each_with_index do |out,index|
      json_string += ",\n    " unless index ==0
      json_string += out.to_json
    end
    json_string += "
    ]  
}"
    return json_string
  end
end
