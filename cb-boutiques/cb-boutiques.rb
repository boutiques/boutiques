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
require 'tool_input_output'
require 'tool_input'
require 'tool_output'
require 'tool_templates'
require 'tool_descriptor'
require 'tool_creator'

def usage
  puts "cbrain_tool_generator: [json_descriptor]"
  exit 
end

################
# Main program #
################

# Inputs parsing
usage if ARGV.length   != 1
json_descriptor         = ARGV[0]

# Templates 
portal_template_file    = "cbrain-templates/portal_tool.rb.erb"
bourreau_template_file  = "cbrain-templates/bourreau_tool.rb.erb"
view_show_template_file = "cbrain-templates/view_show_params.html.erb.erb"
view_task_template_file = "cbrain-templates/view_task_params.html.erb.erb"

# Creates the tool descriptor
tool_descriptor = ToolDescriptor.new
tool_descriptor.parse_from_json File.read(json_descriptor)

# Generates the code of the tool.
tool_templates = ToolTemplates.new portal_template_file,bourreau_template_file,view_show_template_file,view_task_template_file
ToolCreator.create_tool tool_descriptor,tool_templates
