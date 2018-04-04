#!/usr/bin/env python

# Copyright 2015 - 2017:
#   The Royal Institution for the Advancement of Learning McGill University,
#   Centre National de la Recherche Scientifique,
#   University of Southern California,
#   Concordia University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import os
import uuid


class Exporter():

    def __init__(self, descriptor):
        self.descriptor = descriptor

    def convert_type(self, boutiques_type, is_integer=False, is_list=False):
        if is_list:
            return "List"
        if boutiques_type == "Flag":
            return "Boolean"
        if boutiques_type == "Number":
            if is_integer:
                return "Int64"
            return "Double"
        return boutiques_type

    def convert_input_or_output(self, input_or_output, is_output):
        param = {}
        param['name'] = input_or_output.get('name')
        param['id'] = input_or_output.get('id')
        if is_output:
            param['type'] = 'File'
        else:
            param['type'] = self.convert_type(input_or_output.get('type'),
                                              input_or_output.get('integer'),
                                              input_or_output.get('list'))
        param['isOptional'] = input_or_output.get('optional') or False
        param['isReturnedValue'] = is_output
        if input_or_output.get('default-value'):
            param['defaultValue'] = input_or_output.get('default-value')
        if input_or_output.get('description'):
            param['description'] = input_or_output.get('description')
        return param

    def carmin(self, output_file):
        carmin_desc = {}
        with open(self.descriptor, 'r') as fhandle:
            descriptor = json.load(fhandle)

        carmin_desc['identifier'] = str(uuid.uuid4())
        carmin_desc['name'] = descriptor.get('name')
        carmin_desc['version'] = descriptor.get('tool-version')
        carmin_desc['description'] = descriptor.get('description')
        carmin_desc['canExecute'] = True
        carmin_desc['parameters'] = []
        for inp in descriptor.get('inputs'):
            carmin_desc['parameters'].append(
                                        self.convert_input_or_output(inp,
                                                                     False))
        for output in descriptor.get('output-files'):
            carmin_desc['parameters'].append(
                                        self.convert_input_or_output(output,
                                                                     True))
        carmin_desc['properties'] = {}
        carmin_desc['properties']['boutiques'] = True
        if descriptor.get('tags'):
            for prop in descriptor.get('tags').keys():
                carmin_desc['properties'][prop] = descriptor['tags'][prop]
        carmin_desc['errorCodesAndMessages'] = []
        for errors in descriptor.get('error-codes'):
            obj = {}
            obj['errorCode'] = errors['code']
            obj['errorMessage'] = errors['description']
            carmin_desc['errorCodesAndMessages'].append(obj)

        with open(output_file, 'w') as fhandle:
            fhandle.write(json.dumps(carmin_desc, indent=4))
