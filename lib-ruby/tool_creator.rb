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
# Module to create a tool from a ToolDescriptor object and a ToolTemplates object
module ToolCreator

  def ToolCreator.create_tool(tool_descriptor,tool_templates)
    cbrain_tool_name = tool_descriptor.name.downcase.gsub(/[^0-9A-Za-z]/, '')

    # defines the file names
    [cbrain_tool_name, "#{cbrain_tool_name}/portal", "#{cbrain_tool_name}/bourreau", "#{cbrain_tool_name}/views"].each do |dir|
      Dir.mkdir(dir) unless Dir.exists?(dir)
    end

    portal_name    = "#{cbrain_tool_name}/portal/#{cbrain_tool_name}.rb"
    bourreau_name  = "#{cbrain_tool_name}/bourreau/#{cbrain_tool_name}.rb"
    view_show_name = "#{cbrain_tool_name}/views/_show_params.html.erb"
    view_task_name = "#{cbrain_tool_name}/views/_task_params.html.erb"

    # creates the files
    create_file_from_template(tool_templates.get_portal_template,    portal_name,    tool_descriptor)
    create_file_from_template(tool_templates.get_bourreau_template,  bourreau_name,  tool_descriptor)
    create_file_from_template(tool_templates.get_view_show_template, view_show_name, tool_descriptor)
    create_file_from_template(tool_templates.get_view_task_template, view_task_name, tool_descriptor)
  end
  
  private

  def ToolCreator.create_file_from_template(template,file_name,binding_object)
    renderer = ERB.new(template,nil,'-')
    output   = renderer.result(binding_object.get_binding)
    File.open(file_name, 'w') { |file| file.write(output) }
  end

end
