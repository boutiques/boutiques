#!/usr/bin/env python

from argparse import ArgumentParser
from jsonschema import ValidationError
from boutiques.validator import validate_descriptor
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
            elif ("docker" == descriptor["container-image"]["type"] and
                  descriptor["container-image"].get("index")):
                url = descriptor["container-image"]["index"].split("://")[-1]
                descriptor["container-image"]["index"] = url

        if "walltime-estimate" in descriptor.keys():
            descriptor["suggested-resources"] =\
              {"walltime-estimate": descriptor["walltime-estimate"]}
            del descriptor["walltime-estimate"]

        with open(self.output_file, 'w') as fhandle:
            fhandle.write(json.dumps(descriptor, indent=4, sort_keys=True))
        validate_descriptor(self.output_file)

    def get_entry_point(self, app_dir):
        entrypoint = None
        with open(os.path.join(app_dir, "Dockerfile")) as f:
            content = f.readlines()
        for line in content:
            split = line.split()
            if len(split) >= 2 and split[0] == "ENTRYPOINT":
                entrypoint = split[1].strip("[]\"")
        return entrypoint

    def import_bids(self, app_dir):
        path, fil = os.path.split(__file__)
        template_file = os.path.join(path, "templates", "bids-app.json")

        with open(template_file) as f:
            template_string = f.read()

        errors = []
        app_name = os.path.basename(os.path.abspath(app_dir))
        with open(os.path.join(app_dir, "version"), "r") as f:
            version = f.read().strip()
        git_repo = "https://github.com/BIDS-Apps/"+app_name
        entrypoint = self.get_entry_point(app_dir)
        container_image = "bids/"+app_name
        analysis_types = "participant\", \"group\", \"session"

        if not entrypoint:
            errors.append("No entrypoint found in container.")

        if len(errors):
            raise ValidationError("Invalid descriptor:\n"+"\n".join(errors))

        template_string = template_string.replace("@@APP_NAME@@", app_name)
        template_string = template_string.replace("@@VERSION@@", version)
        template_string = template_string.replace("@@GIT_REPO_URL@@", git_repo)
        template_string = template_string.replace("@@DOCKER_ENTRYPOINT@@",
                                                  entrypoint)
        template_string = template_string.replace("@@CONTAINER_IMAGE@@",
                                                  container_image)
        template_string = template_string.replace("@@ANALYSIS_TYPES@@",
                                                  analysis_types)

        with open(self.output_file, "w") as f:
            f.write(template_string)
