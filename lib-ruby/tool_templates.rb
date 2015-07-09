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
require 'erb'


# Class handling the templates used to generate the code of the Tool
class ToolTemplates

  def initialize(portal_template_file,bourreau_template_file,view_show_template_file,view_task_template_file)
    @portal_template_file    = portal_template_file        # the template file name for the portal implementation of the Tool
    @bourreau_template_file  = bourreau_template_file      # the template file name for the bourreau implementation of the Tool
    @view_show_template_file = view_show_template_file     # the template file name for the view/show implementation of the Tool
    @view_task_template_file = view_task_template_file     # the template file name for the view/task implementation of the Tool
  end

  #########################
  # All the get_* methods #
  #########################

  def get_portal_template
    get_template_from_file(@portal_template,@portal_template_file)
  end

  def get_bourreau_template
    get_template_from_file(@bourreau_template,@bourreau_template_file)
  end

  def get_view_show_template
    get_template_from_file(@view_show_template,@view_show_template_file)
  end

  def get_view_task_template
    get_template_from_file(@view_task_template,@view_task_template_file)
  end
  
  private
  # to avoid reading several times the same file
  def get_template_from_file(class_variable,file_name)
    return class_variable unless class_variable == nil
    class_variable = File.read(file_name)
    return class_variable
  end  

end
