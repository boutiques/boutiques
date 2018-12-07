#!/usr/bin/env python

from argparse import ArgumentParser
from jsonschema import ValidationError
from boutiques.validator import validate_descriptor
from boutiques.localExec import loadJson
from boutiques.logger import raise_error
import boutiques
import yaml
import json
import os
import os.path as op


class ImportError(Exception):
    pass


class Importer():

    def __init__(self, input_descriptor, output_descriptor,
                 input_invocation, output_invocation):
        self.input_descriptor = input_descriptor
        self.output_descriptor = output_descriptor
        self.input_invocation = input_invocation
        self.output_invocation = output_invocation

    def upgrade_04(self):
        """
         Differences between 0.4 and current (0.5):
           -schema version (obv)
           -singularity should now be represented same as docker
           -walltime should be part of suggested_resources structure

        I.e.
        "schema-version": "0.4",
                    ...... becomes.....
        "schema-version": "0.5",

        I.e.
        "container-image": {
          "type": "singularity",
          "url": "shub://gkiar/ndmg-cbrain:master"
          },
                    ...... becomes.....
        "container-image": {
          "type": "singularity",
          "image": "gkiar/ndmg-cbrain:master",
          "index": "shub://",
        },

        I.e.
        "walltime-estimate": 3600,
                    ...... becomes.....
        "suggested-resources": {
          "walltime-estimate": 3600
        },
        """
        descriptor = loadJson(self.input_descriptor)

        if descriptor["schema-version"] != "0.4":
            raise_error(ImportError, "The input descriptor must have "
                        "'schema-version'=0.4")
        descriptor["schema-version"] = "0.5"

        if "container-image" in descriptor.keys():
            if "singularity" == descriptor["container-image"]["type"]:
                url = descriptor["container-image"]["url"]
                img = url.split("://")
                if len(img) == 1:
                    descriptor["container-image"]["image"] = img[0]
                elif len(img) == 2:
                    descriptor["container-image"]["image"] = img[1]
                    descriptor["container-image"]["index"] = img[0] + "://"
                del descriptor["container-image"]["url"]
            elif ("docker" == descriptor["container-image"]["type"] and
                  descriptor["container-image"].get("index")):
                url = descriptor["container-image"]["index"].split("://")[-1]
                descriptor["container-image"]["index"] = url

        if "walltime-estimate" in descriptor.keys():
            descriptor["suggested-resources"] =\
              {"walltime-estimate": descriptor["walltime-estimate"]}
            del descriptor["walltime-estimate"]

        with open(self.output_descriptor, 'w') as fhandle:
            fhandle.write(json.dumps(descriptor, indent=4, sort_keys=True))
        validate_descriptor(self.output_descriptor)

    def get_entry_point(self, input_descriptor):
        entrypoint = None
        with open(os.path.join(self.input_descriptor, "Dockerfile")) as f:
            content = f.readlines()
        for line in content:
            split = line.split()
            if len(split) >= 2 and split[0] == "ENTRYPOINT":
                entrypoint = split[1].strip("[]\"")
        return entrypoint

    def import_bids(self):
        path, fil = os.path.split(__file__)
        template_file = os.path.join(path, "templates", "bids-app.json")

        with open(template_file) as f:
            template_string = f.read()

        errors = []
        app_name = os.path.basename(os.path.abspath(self.input_descriptor))
        version = 'unknown'
        version_file = os.path.join(self.input_descriptor, "version")
        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                version = f.read().strip()
        git_repo = "https://github.com/BIDS-Apps/"+app_name
        entrypoint = self.get_entry_point(self.input_descriptor)
        container_image = "bids/"+app_name
        analysis_types = "participant\", \"group\", \"session"

        if not entrypoint:
            errors.append("No entrypoint found in container.")

        if len(errors):
            raise_error(ValidationError, "Invalid descriptor:\n"+"\n".
                        join(errors))

        template_string = template_string.replace("@@APP_NAME@@", app_name)
        template_string = template_string.replace("@@VERSION@@", version)
        template_string = template_string.replace("@@GIT_REPO_URL@@", git_repo)
        template_string = template_string.replace("@@DOCKER_ENTRYPOINT@@",
                                                  entrypoint)
        template_string = template_string.replace("@@CONTAINER_IMAGE@@",
                                                  container_image)
        template_string = template_string.replace("@@ANALYSIS_TYPES@@",
                                                  analysis_types)

        with open(self.output_descriptor, "w") as f:
            f.write(template_string)

    def import_cwl(self):

        # Read the CWL descriptor
        with open(self.input_descriptor, 'r') as f:
            cwl_desc = yaml.load(f)

        # validate yaml descriptor?

        bout_desc = {}
        # Command line
        if cwl_desc.get('baseCommand') is None:
            raise_error(ImportError, 'Cannot find baseCommand attribute, '
                        'perhaps you passed a workflow document, '
                        'this is not supported')
        if type(cwl_desc['baseCommand']) is list:
            command_line = ""
            for i in cwl_desc['baseCommand']:
                command_line += i+" "
        else:
            command_line = cwl_desc['baseCommand']
        if cwl_desc.get('arguments'):
            for i in cwl_desc['arguments']:
                if type(i) is dict:
                    raise_error(ImportError, 'Dict arguments not supported.')
                if "$(runtime." in i:
                    raise_error(ImportError, 'Runtime parameters '
                                ' are not supported:'
                                " "+i)
                command_line += i+" "
        boutiques_inputs = []

        # Inputs
        def position(x):
            if (type(x) is dict and
                    x.get('inputBinding') and
                    x['inputBinding'].get('position')):
                return x['inputBinding']['position']
            return 0
        sorted_inputs = sorted(cwl_desc['inputs'],
                               key=lambda x: (position(cwl_desc['inputs'][x])))
        # Mapping between CQL and Boutiques input types
        boutiques_types = {
          'string': 'String',
          'File': 'File',
          'File?': 'File',
          'boolean': 'Flag',
          'int': 'Number'
          # float type?
        }
        for cwl_input in sorted_inputs:
            bout_input = {}
            # Easy stuff
            bout_input['id'] = cwl_input  # perhaps 'idify' that
            cwl_in_obj = cwl_desc['inputs'][cwl_input]
            if type(cwl_in_obj) is dict and cwl_in_obj.get('name'):
                bout_input['name'] = cwl_in_obj['name']
            else:
                bout_input['name'] = cwl_input
            value_key = "[{0}]".format(cwl_input.upper())
            if (type(cwl_in_obj) is dict and
                    cwl_in_obj.get('inputBinding') is not None):
                command_line += " "+value_key
            bout_input['value-key'] = value_key

            # CWL type parsing
            if type(cwl_in_obj) is dict:
                cwl_type = cwl_in_obj['type']
            else:
                cwl_type = 'string'
            if type(cwl_type) is dict:  # It must be an array
                if cwl_type['type'] != "array":
                    raise_error(ImportError, "Only 1-level nested "
                                "types of type"
                                " 'array' are supported (CWL input: {0})".
                                format(cwl_input))
                if cwl_type.get('inputBinding') is not None:
                    raise_error(ImportError, "Input bindings of "
                                "array elements "
                                "are not supported (CWL input: {0})".
                                format(cwl_input))
                cwl_type = cwl_type['items']
                bout_input['list'] = True
            if type(cwl_type) != str:
                    raise_error(ImportError, "Unknown type:"
                                " {0}".format(str(cwl_type)))
            boutiques_type = boutiques_types[cwl_type.replace("[]", "")
                                                     .replace("?", "")]
            bout_input['type'] = boutiques_type
            if cwl_type == 'int':
                bout_input['integer'] = True
            if '?' in cwl_type or boutiques_type == "Flag":
                bout_input['optional'] = True

            # CWL input binding
            if type(cwl_in_obj) is dict:
                cwl_input_binding = cwl_in_obj['inputBinding']
            else:
                cwl_input_binding = {}
            if cwl_input_binding.get('prefix'):
                bout_input['command-line-flag'] = cwl_input_binding['prefix']
                if (not (cwl_input_binding.get('separate') is None) and
                        cwl_input_binding['separate'] is False):
                    bout_input['command-line-flag-separator'] = ''
            boutiques_inputs.append(bout_input)

            # array types
            if cwl_type.endswith("[]"):
                bout_input['list'] = True
                if cwl_input_binding.get("itemSeparator"):
                    if cwl_input_binding['itemSeparator'] != ' ':
                        raise_error(ImportError, 'Array separators wont be '
                                    'supported until #76 is implemented')

        # Outputs

        def resolve_glob(glob, boutiques_inputs):
            if not glob.startswith("$"):
                return glob
            if not glob.startswith("$(inputs."):
                raise_error(ImportError, "Unsupported reference: "+glob)
            input_id = glob.replace("$(inputs.", "").replace(")", "")
            for i in boutiques_inputs:
                if i['id'] == input_id:
                    return i['value-key']
            raise_error(ImportError, "Unresolved reference"
                        " in glob: " + glob)

        boutiques_outputs = []
        sorted_outputs = sorted(cwl_desc['outputs'],
                                key=(lambda x: cwl_desc['outputs'][x].
                                     get('outputBinding')))
        for cwl_output in sorted_outputs:
            bout_output = {}
            bout_output['id'] = cwl_output  # perhaps 'idify' that
            if cwl_desc['outputs'][cwl_output].get('name'):
                bout_output['name'] = cwl_desc['outputs'][cwl_output]['name']
            else:
                bout_output['name'] = cwl_output
            cwl_out_binding = (cwl_desc['outputs'][cwl_output].
                               get('outputBinding'))
            if cwl_out_binding and cwl_out_binding.get('glob'):
                glob = cwl_out_binding['glob']
                bout_output['path-template'] = resolve_glob(glob,
                                                            boutiques_inputs)
                cwl_out_obj = cwl_desc['outputs'][cwl_output]
                if type(cwl_out_obj.get('type')) is dict:
                    if (cwl_out_obj['type'].get('type')
                       and cwl_out_obj['type']['type'] == 'array'):
                            bout_output['list'] = True
                    else:
                        raise_error(ImportError, 'Unsupported output type: '
                                    + cwl_output['type'])
                boutiques_outputs.append(bout_output)
        # Boutiques descriptors have to have at least 1 output file
        if len(boutiques_outputs) == 0 or cwl_desc.get('stdout'):
            stdout = cwl_desc.get('stdout') or 'stdout.txt'
            command_line += " > "+stdout
            boutiques_outputs.append(
              {
                  'id': 'stdout',
                  'name': 'Standard output',
                  'path-template': 'stdout.txt'
              }
            )

        # Mandatory boutiques fields
        bout_desc['command-line'] = command_line
        if cwl_desc.get("doc"):
            bout_desc['description'] = (cwl_desc.get("doc").
                                        replace(os.linesep, ''))
        else:
            bout_desc['description'] = "Tool imported from CWL."
        bout_desc['inputs'] = boutiques_inputs
        # This may not be a great idea but not sure if CWL tools have names
        bout_desc['name'] = op.splitext(op.basename(self.input_descriptor))[0]
        bout_desc['output-files'] = boutiques_outputs
        bout_desc['schema-version'] = '0.5'
        bout_desc['tool-version'] = "unknown"  # perhaphs there's one in cwl

        # Hints and requirements
        def parse_req(req, req_type, bout_desc):
            # We could support InitialWorkDirRequiment, through config files
            if req_type == 'DockerRequirement':
                container_image = {}
                container_image['type'] = 'docker'
                container_image['index'] = 'index.docker.io'
                container_image['image'] = req['dockerPull']
                bout_desc['container-image'] = container_image
                return
            if req_type == 'EnvVarRequirement':
                bout_envars = []
                for env_var in req['envDef']:
                    bout_env_var = {}
                    bout_env_var['name'] = env_var
                    bout_env_var['value'] = resolve_glob(
                                              req['envDef'][env_var],
                                              boutiques_inputs)
                    bout_envars.append(bout_env_var)
                    bout_desc['environment-variables'] = bout_envars
                return
            if req_type == 'ResourceRequirement':
                suggested_resources = {}
                if req.get('ramMin'):
                    suggested_resources['ram'] = req['ramMin']
                if req.get('coresMin'):
                    suggeseted_resources['cpu-cores'] = req['coresMin']
                bout_desc['suggested-resources'] = suggested_resources
                return
            if req_type == 'InitialWorkDirRequirement':
                listing = req.get('listing')
                for entry in listing:
                    file_name = entry.get('entryname')
                    assert(file_name is not None)
                    template = entry.get('entry')
                    for i in boutiques_inputs:
                        if i.get("value-key"):
                            template = template.replace("$(inputs."+i['id']+")",
                                                        i.get("value-key"))
                    template = template.split(os.linesep)
                    assert(template is not None)
                    name = op.splitext(file_name)[0]
                    boutiques_outputs.append(
                        {
                            'id': name,
                            'name': name,
                            'path-template': file_name,
                            'file-template': template
                        })
                return
            raise_error(ImportError, 'Unsupported requirement: '+str(req))

        for key in ['requirements', 'hints']:
            if(cwl_desc.get(key)):
                for i in cwl_desc[key]:
                    parse_req(cwl_desc[key][i], i, bout_desc)

        # enum types?

        # Write descriptor
        with open(self.output_descriptor, 'w') as f:
            f.write(json.dumps(bout_desc, indent=4, sort_keys=True))
        validate_descriptor(self.output_descriptor)

        if self.input_invocation is None:
            return

        # Convert invocation
        def get_input(descriptor_inputs, input_id):
            for inp in descriptor_inputs:
                if inp['id'] == input_id:
                    return inp
            return False
        boutiques_invocation = {}
        with open(self.input_invocation, 'r') as f:
            cwl_inputs = yaml.load(f)
        for input_name in cwl_inputs:
            if get_input(bout_desc['inputs'], input_name)['type'] != "File":
                input_value = cwl_inputs[input_name]
            else:
                input_value = cwl_inputs[input_name]['path']
            boutiques_invocation[input_name] = input_value
        with open(self.output_invocation, 'w') as f:
            f.write(json.dumps(boutiques_invocation, indent=4, sort_keys=True))
        boutiques.invocation(self.output_descriptor,
                             "-i", self.output_invocation)
