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

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from jsonschema import ValidationError
from boutiques.validator import validate_json
from git import Repo
import git, json, os, sys

class Publisher():

    def __init__(self, boutiques_dir, remote_name=None, author=None, base_url=None):
        self.boutiques_dir = os.path.abspath(boutiques_dir)
        self.remote_name = remote_name if remote_name else 'origin'
        self.author = author
        self.base_url = base_url
        try:
            self.boutiques_repo = Repo(self.boutiques_dir)
        except git.exc.InvalidGitRepositoryError as e:
              sys.stderr.write('error: %s is not a Git repository.\n' % self.boutiques_dir)
              sys.exit(1)

        for remote in self.boutiques_repo.remotes:
            if remote.name == self.remote_name:
                self.boutiques_remote = remote

        if not self.base_url:
            url = self.boutiques_remote.url.replace(".git","").replace("git@github.com:","http://github.com/")
            url = url.replace("http://github.com", "https://raw.githubusercontent.com")
            url += "/master"
            self.base_url = url

        if not self.author:
            self.author = self.boutiques_repo.head.commit.author.name

            
    def get_infos_from_descriptor(self, descriptor_file):
        with open(descriptor_file, 'r') as f:
            descriptor_json_string = json.loads(f.read())
        return descriptor_json_string.get("name"),\
               descriptor_json_string.get("description")

    def find_json_files(self, directory):
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".json"):
                    json_files.append(os.path.join(root, file))
        return json_files
    
    def get_owl_string(self, label, description, author, url):

        path, fil = os.path.split(__file__)
        template_file = os.path.join(path, "neurolinks-template", "tool.owl")

        with open(template_file) as f:
            template_string = f.read()

        template_string = template_string.replace("@@__LABEL__@@", label)
        template_string = template_string.replace("@@__DESCRIPTION__@@", description)
        template_string = template_string.replace("@@__AUTHOR__@@", author)
        template_string = template_string.replace("@@__URL__@@", url)

        return template_string

    def is_boutiques_descriptor(self, json_file):
        try:
            validate_json(json_file)
            return True
        except:
            return False
    
    def get_owl_strings(self):
        owl_strings = []
        json_files = self.find_json_files(self.boutiques_dir)
        descriptors = [ x for x in json_files if self.is_boutiques_descriptor(x) ]
        for descriptor in descriptors:
            label,description = self.get_infos_from_descriptor(descriptor)
            author = self.author
            url = self.get_url(descriptor)
            owl_strings.append(self.get_owl_string(label, description, author, url))
        return owl_strings
        
    def get_url(self, file_path):
        file_path = file_path.replace(self.boutiques_dir,"")
        url = self.base_url + file_path
        return url
    
    def publish(self):
        owl_strings = self.get_owl_strings()
        neurolinks = "https://github.com/brainhack101/neurolinks"
        tool_owl = "owls/tool.owl"
        print("\nTo publish the Boutiques tools in {0}:\n\
1. fork and clone {1}\n\
2. append the following content to {2}\n\
3. commit and make a pull request\n".format(
            self.boutiques_dir, neurolinks, tool_owl))
        for o in owl_strings:
            print(o)
    
def main(args=None):
    parser = ArgumentParser("Boutiques Publisher", formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("--boutiques-repo", "-b", action="store",
                        default='.',
                        help="Local path to a Git repo containing Boutiques descriptors to publish.")
    parser.add_argument("--remote-name", "-r", action="store",
                        default='origin',
                        help="Remote name to use in Git repo to get URL of Boutiques descriptor.")
    parser.add_argument("--author", "-a", action="store",
                        help="Author name (default: author of last commit in Git repo).")
    results = parser.parse_args() if args is None else parser.parse_args(args)
    publisher = Publisher(results.boutiques_repo, results.remote_name, results.author).publish()
            
# Execute program
if  __name__ == "__main__":
    main()
