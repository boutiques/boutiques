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
# Class describing the output of a Tool
class ToolOutput < ToolInputOutput

  def initialize(name,description,command_line_key,path_template,list,optional,command_line_flag)
    super(name,description,command_line_key,list,optional,command_line_flag)
    @path_template     = path_template # the template used to generate output file names
    @resolved_template = @path_template.dup
  end

  #######################
  # Getters and Setters #
  #######################

  def get_path_template
    return @path_template 
  end

  def get_resolved_template
    return @resolved_template
  end
  
  def set_resolved_template value
    @resolved_template = value
  end

end
