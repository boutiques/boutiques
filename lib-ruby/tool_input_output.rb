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
# Super class for tool Inputs and Outputs

class ToolInputOutput

  def initialize(name,description,command_line_key,list,optional,command_line_flag)
    @name              = name.gsub(/[^0-9A-Za-z]/, '')  # Should be usable as a Ruby variable name.
    @description       = description
    @command_line_key  = command_line_key
    @list              = list
    @optional          = optional
    @command_line_flag = command_line_flag
  end
  
  ###########
  # Getters #
  ###########

  def get_name
    return @name
  end
  
  def get_description
    return @description
  end
  
  def get_command_line_key
    return @command_line_key
  end
  
  def is_list?
    return @list
  end
  
  def is_optional?
    return @optional
  end
  
  def get_command_line_flag
    return @command_line_flag
  end

  private
   
end
