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

from argparse import ArgumentParser
from jsonschema import ValidationError
from boutiques.validator import validate_json
import json
import os


class Importer():

    def __init__(self, output_file):
        self.output_file = output_file
    
    def upgrade_04(self, input_file):
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
        with open(input_file, 'r') as fhandle:
            descriptor = json.load(fhandle)

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
            elif "docker" == descriptor["container-image"]["type"] and descriptor["container-image"].get("index"):
                url = descriptor["container-image"]["index"] = descriptor["container-image"]["index"].split("://")[-1]

        if "walltime-estimate" in descriptor.keys():
            descriptor["suggested-resources"] = {"walltime-estimate": descriptor["walltime-estimate"]}
            del descriptor["walltime-estimate"]

        with open(self.output_file, 'w') as fhandle:
            fhandle.write(json.dumps(descriptor, indent=4))
        validate_json(self.output_file)

    def get_entry_point(self, app_dir):
        entrypoint = None
        with open(os.path.join(app_dir,"Dockerfile")) as f:
            content = f.readlines()
        for line in content:
            split = line.split()
            if len(split) >=2 and split[0] == "ENTRYPOINT":
                entrypoint = split[1].strip("[]\"")
        return entrypoint
            
    def import_bids(self, app_dir):
        path, fil = os.path.split(__file__)
        template_file = os.path.join(path, "bids-app-template", "template.json")

        with open(template_file) as f:
            template_string = f.read()

        errors = []
        app_name = os.path.basename(os.path.abspath(app_dir))
        with open(os.path.join(app_dir,"version"),"r") as f:
            version = f.read().strip()
        git_repo = "https://github.com/BIDS-Apps/"+app_name
        entrypoint = self.get_entry_point(app_dir)
        container_image = "bids/"+app_name
        analysis_types = "participant\", \"group\", \"session"

        if not entrypoint:
            errors.append("No entrypoint found in container.") 
        
        if len(errors):
            raise ValidationError("Invalid descriptor:\n"+"\n".join(errors))

        template_string = template_string.replace("@@APP_NAME@@",app_name)
        template_string = template_string.replace("@@VERSION@@",version)
        template_string = template_string.replace("@@GIT_REPO_URL@@",git_repo)
        template_string = template_string.replace("@@DOCKER_ENTRYPOINT@@",entrypoint)
        template_string = template_string.replace("@@CONTAINER_IMAGE@@",container_image)
        template_string = template_string.replace("@@ANALYSIS_TYPES@@",analysis_types)

        with open(self.output_file,"w") as f:
            f.write(template_string)

        
def main(args=None):

    # Arguments parsing
    parser = ArgumentParser()
    parser.add_argument("importing", help="Type of import we are performing",
                        choices=['bids', '0.4'])
    parser.add_argument("output_file", help="File where the Boutiques descriptor will be written.")
    parser.add_argument("--input_file", help="File for existing Boutiques descriptor of older version")
    parser.add_argument("--bids_app_dir", help="Root directory of the BIDS app to import.")
    results = parser.parse_args() if args is None else parser.parse_args(args)

    importer = Importer(results.output_file)
    if results.importing == '0.4':
        importer.upgrade_04(results.input_file)
    elif results.importing == 'bids':
        importer.import_bids(results.bids_app_dir)

# Execute program
if  __name__ == "__main__":
    main()
