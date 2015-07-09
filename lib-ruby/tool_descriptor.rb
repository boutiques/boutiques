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
  
  def parse_from_json(json_object)
    # TODO json validation goes here
    hash            = JSON.parse(json_object)
    @name           = hash["name"].gsub(/[^0-9A-Za-z]/,'')
    @tool_version   = hash["tool-version"]
    @description    = hash["description"]
    @command_line   = hash["command-line"]
    @docker_image   = hash["docker-image"]
    @docker_index   = hash["docker-index"]
    @schema_version = hash["schema-version"]
  
    @inputs = Array.new
    hash["inputs"].each do |input_hash|
      @inputs << ToolInput.new(
        input_hash["name"],
        input_hash["type"],
        input_hash["description"],
        input_hash["command-line-key"],
        input_hash["list"],
        input_hash["optional"],
        input_hash["command-line-flag"]
      )
    end
  
    @outputs = Array.new
    hash["output-files"].each do |output_hash|
      @outputs << ToolOutput.new(
        output_hash["name"],
        output_hash["description"],
        output_hash["command-line-key"],
        output_hash["path-template"],
        output_hash["list"],
        output_hash["optional"],
        output_hash["command-line-flag"]
      )
    end   
  end

  #########################
  #       Getters         #
  #########################

  def get_name
    return @name
  end

  def get_tool_version
    return @tool_version
  end
  
  def get_description
    return @description
  end

  def get_command_line
    return @command_line
  end

  def get_docker_image
    return @docker_image
  end

  def get_docker_index
    return @docker_index
  end

  def get_schema_version
    return @schema_version
  end
  
  def get_inputs
    return @inputs
  end
  
  def get_outputs
    return @outputs
  end
  
  def get_binding
    return binding()
  end

end
