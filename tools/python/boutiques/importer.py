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
import os


class Importer():

    def __init__(self,app_dir,output_file):
        self.app_dir = app_dir
        path, fil = os.path.split(__file__)
        self.template_file = os.path.join(path, "bids-app-template", "template.json")
        self.output_file = output_file

    def get_entry_point(self):
        entrypoint = None
        with open(os.path.join(self.app_dir,"Dockerfile")) as f:
            content = f.readlines()
        for line in content:
            split = line.split()
            if len(split) >=2 and split[0] == "ENTRYPOINT":
                entrypoint = split[1].strip("[]\"")
        return entrypoint
            
    def import_bids(self):
        with open(self.template_file) as f:
            template_string = f.read()

        errors = []
        app_name = os.path.basename(self.app_dir)
        with open(os.path.join(self.app_dir,"version"),"r") as f:
            version = f.read().strip()
        git_repo = "https://github.com/BIDS-Apps/"+app_name
        entrypoint = self.get_entry_point()
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
    parser.add_argument("bids_app_dir", help="Root directory of the BIDS app to import.")
    parser.add_argument("output_file", help="File where the Boutiques descriptor will be written.")
    results = parser.parse_args() if args is None else parser.parse_args(args)
    
    importer = Importer(results.bids_app_dir,results.output_file)
    importer.import_bids()

# Execute program
if  __name__ == "__main__":
    main()
