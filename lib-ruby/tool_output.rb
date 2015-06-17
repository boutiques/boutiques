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

  def initialize(name,type,syntax_key,template,documentation,cardinality,optional,command_line_flag)
    raise "Output type has to be \"File\" or \"Directory\"" unless type == "File" || type == "Directory" 
    super(name,type,syntax_key,documentation,cardinality,optional,command_line_flag)
    @template          = template # the template used to generate output file names
    @resolved_template = @template.dup
  end

  ###################################
  # All the get_* and set_* methods #
  ###################################

  def get_template
    return @template 
  end

  def get_resolved_template
    return @resolved_template
  end
  
  def set_resolved_template value
    @resolved_template = value
  end

end
