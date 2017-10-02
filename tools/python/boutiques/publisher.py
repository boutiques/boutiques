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
from boutiques.validator import validate_descriptor
from git import Repo
from github import Github
import git, json, os, sys
try:
    # For Python 3.0 and later
    from urllib.request import urlopen, URLError
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, URLError

class Publisher():

    def __init__(self, boutiques_dir, remote_name, tool_author, tool_url, inter,
                 neurolinks_repo_url, neurolinks_dest_path, github_user, github_password, no_github):
        self.boutiques_dir = os.path.abspath(boutiques_dir)
        self.remote_name = remote_name if remote_name else 'origin'
        try:
            self.boutiques_repo = Repo(self.boutiques_dir)
        except git.exc.InvalidGitRepositoryError as e:
            # We won't publish a descriptor which is not in a Git repo!
            sys.stderr.write('error: %s is not a Git repository.\n' % self.boutiques_dir)
            sys.exit(1)

        for remote in self.boutiques_repo.remotes:
            if remote.name == self.remote_name:
                self.boutiques_remote = remote

        url = self.boutiques_remote.url
        # If remote URL is on Github, try to guess the URL of the Boutiques descriptor
        if "github.com" in url: 
            url = url.replace(".git","").replace("git@github.com:","https://github.com/")
            url = url.replace("https://github.com/", "https://raw.githubusercontent.com/")
            url = url.replace("http://github.com/", "https://raw.githubusercontent.com/")
            url += "master"
        self.base_url = url

        # Try to guess the tool author
        self.tool_author = tool_author

        self.tool_url = tool_url if tool_url else "http://example.com"
        self.inter = inter
        self.no_github = no_github

        if self.no_github:
            return

        # Set github credentials
        self.github_user = github_user
        self.github_password = github_password
        self.fix_github_credentials()
        # Fork and clone the neurolinks repo
        if neurolinks_repo_url.startswith("http"):
            fork_url = self.fork_repo(neurolinks_repo_url) # won't do anything if fork already exists
            neurolinks_local_url = self.clone_repo(fork_url, neurolinks_dest_path)
            # Add base neurolinks repo as remote and pull from it, in case
            # fork already existed and is outdated
            self.neurolinks_repo = Repo(neurolinks_local_url)
            base = self.neurolinks_repo.create_remote('base', neurolinks_repo_url)
            neurolinks_repo_url = neurolinks_local_url
        else:
            self.neurolinks_repo = Repo(neurolinks_repo_url)
        self.neurolinks_repo.remotes.base.pull('master')
        
        self.tools_file = os.path.abspath(os.path.join(neurolinks_repo_url,
                                                       'jsons', 'tool.json'))
        if not os.path.isfile(self.tools_file):
            print("error: cannot find {0} (check neurolinks repo).".format(self.tools_file))
            sys.exit(1)
            
    def fix_github_credentials(self):
        pygithub_file = os.path.join(os.getenv("HOME"),".pygithub")
        # Read saved credentials
        try:
            with open(pygithub_file,"r") as f:
                json_creds = json.load(f)
        except IOError:
            json_creds = {}
        except ValueError:
            json_creds = {}
        # Credentials passed as parameters have precedence. Ask credentials if none
        # can be found
        username = self.github_user if self.github_user else json_creds.get('user')
        if not username:
            username = self.get_from_stdin("GitHub login")
        password = self.github_password if self.github_password else json_creds.get('password')
        if not password:
            password = self.get_from_stdin("GitHub password (user: {0})".format(username))
        # Save credentials
        self.github_username = username
        self.github_password = password
        json_creds['user'] = self.github_username
        json_creds['password'] = self.github_password
        with open(pygithub_file,"w") as f:
            f.write(json.dumps(json_creds, indent=4, sort_keys=True))
        
    def find_json_files(self, directory):
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".json"):
                    json_files.append(os.path.join(root, file))
        return json_files
    
    def get_json_string(self, identifier, label, description, tool_author, tool_url, boutiques_url, docker_container, singularity_container):

        path, fil = os.path.split(__file__)
        template_file = os.path.join(path, "neurolinks-template", "tool.json")

        with open(template_file) as f:
            template_string = f.read()

        template_string = template_string.replace("@@__ID__@@", identifier)
        template_string = template_string.replace("@@__LABEL__@@", label)
        template_string = template_string.replace("@@__DESCRIPTION__@@", description)
        template_string = template_string.replace("@@__TOOL_AUTHOR__@@", tool_author)
        template_string = template_string.replace("@@__TOOL_URL__@@", tool_url)
        template_string = template_string.replace("@@__BOUTIQUES_URL__@@", boutiques_url)

        json_string = json.loads(template_string)
        if docker_container:
            json_string['dockercontainer'] = docker_container
        if singularity_container:
            json_string['singularitycontainer'] = singularity_container
            
        return json_string

    def is_boutiques_descriptor(self, json_file):
        try:
            validate_descriptor(json_file)
            return True
        except:
            return False

    def get_from_stdin(self, question, default_value=None, input_type=None):
        if not self.inter:
            return default_value
        prompt = question+" ("+default_value+"): " if default_value else question+": "
        try:
            answer = raw_input(prompt) # Python 2
        except NameError:
            answer = input(prompt) # Python 3
        answer = answer if answer else default_value
        if input_type == "URL":
            while not self.check_url(answer):
                answer = self.get_from_stdin(question, default_value, input_type)
        return answer

    def check_url(self, url):
        try:
            code = urlopen(url).getcode()
        except ValueError as e:
            print("error: {0}".format(e.message))
            return False
        except URLError as e:
            print("error: {0}".format(e.message))
            return False
        if code != 200:
            print("warning: URL is not accessible (status: {0})".format(code))
            return False
        else:
            print("  ... URL is accessible.")
            return True
            
    
    def print_banner(self, descriptor):
        name = descriptor['name']
        text = "Found Boutiques tool {0}".format(name,"")
        line = ""
        for i in range(0, len(text)):
            line = line + "="
        print("")
        print(line)
        print(text)
        print(line)
        
    def get_descriptors(self):
        json_strings = []
        json_files = self.find_json_files(self.boutiques_dir)
        descriptors = [ x for x in json_files if self.is_boutiques_descriptor(x) ]
        return descriptors

    def get_neurolinks_json(self, descriptor_file_name, tools):
        entities = tools.get('entities')
        with open(descriptor_file_name, "r") as f:
            descriptor = json.load(f)
        self.print_banner(descriptor)
        if self.inter:
            if(self.get_from_stdin("Publish Y/n?","Y") != "Y"):
                return None
        if(self.contains(descriptor['name'],entities)):
            if not self.inter:
                print('Not overwriting existing entry - use interactive mode to override')
                return None
            if(self.get_from_stdin("{0} is already published, overwrite Y/n?".format(
                    descriptor['name']),"n") != "Y"):
                return None
            tools['entities'] = self.remove(descriptor['name'], entities)
        label = descriptor['name']
        description = descriptor.get('description')
        docker_container = None
        singularity_container = None
        container_image = descriptor.get('container-image')
        if container_image:
            if container_image.get('type') == "docker":
                index = container_image.get('index') if container_image.get('index') else 'http://index.docker.io'
                if "index.docker.io" in index:
                    index = "https://hub.docker.com/r/"
                elif "quay.io" in index:
                    index = "https://quay.io/repository"
                docker_container = os.path.join(index,container_image.get("image").split(':')[0])
            if container_image.get('type') == "singularity":
                index = container_image.get('index') if container_image.get('index') else 'shub://'
                if index == "docker://":
                    singularity_container = os.path.join("https://hub.docker.com",container_image.get("image").split(':')[0]) 
                else:
                    singularity_container = os.path.join(index,container_image.get("image")) 
        identifier = label.replace(" ","_")
        boutiques_url = self.get_url(descriptor_file_name)
        if self.inter:
            self.tool_author = self.get_from_stdin("Tool author",
                                                   self.tool_author)
            self.tool_url = self.get_from_stdin("Tool URL", self.tool_url, "URL")
            boutiques_url = self.get_from_stdin("Boutiques descriptor URL",
                                                boutiques_url, "URL")
        return self.get_json_string(identifier, label, description,
                                                 self.tool_author, self.tool_url,
                                                 boutiques_url, docker_container, singularity_container)
    def get_url(self, file_path):
        file_path = file_path.replace(self.boutiques_dir,"")
        url = self.base_url + file_path
        return url

    def contains(self, label, tools):
        if not tools:
            return
        for tool in tools:
            if tool['label'] == label:
                return True
        return False

    def remove(self, label, tools):
        new_tools = [ x for x in tools if x['label'] != label ]
        return new_tools
    
    def publish(self):
        json_tools = []
        existing_tools = {}
        if not self.no_github:
            # Load existing tools
            with open(self.tools_file, "r") as json_file:
                existing_tools = json.load(json_file)
        # Get new tools from boutiques repo
        descriptors = self.get_descriptors()
        for descriptor_file_name in descriptors:
            # Build neurolinks string
            neurolinks_json = self.get_neurolinks_json(descriptor_file_name, existing_tools)
            # Have user review before commit
            if not self.inter and neurolinks_json:
                print("Tool summary:")
                print(json.dumps(neurolinks_json, indent=4, sort_keys=True))
                if(self.get_from_stdin("Publish Y/n?","n") != "Y"):
                    neurolinks_json = None
            # Publish json string unless user didn't want to
            if neurolinks_json:
                json_tools.append(neurolinks_json)
        if len(json_tools) == 0:
            print("Nothing to publish, bye!")
            return
        if self.no_github:
            for tool in json_tools:
                print(json.dumps(tool, indent=4, sort_keys=True))
            return
        # Add new tools to existing tools
        for tool in json_tools:
            existing_tools['entities'].append(tool)
        # Write updated tools
        json_file = open(self.tools_file, "w")
        json_file.write(json.dumps(existing_tools, indent=4, sort_keys=True))
        json_file.close()
        # Commit tools file
        self.neurolinks_repo.index.add([self.tools_file])
        self.neurolinks_repo.index.commit("Added tool {0} with bosh-publish".format(tool['label']))
        # Push to fork
        self.neurolinks_repo.remotes.origin.push()
        # Make PR
        self.pr(self.neurolinks_repo.remotes.origin.url,
                self.neurolinks_repo.remotes.base.url)
            
    def clone_repo(self, repo_url, dest_path):
        print("Cloning {0} to {1}...".format(repo_url,dest_path))
        Repo.clone_from(repo_url, dest_path)
        return os.path.abspath(dest_path)

    def fork_repo(self, repo_url):
        print("Forking {0} to {1}...".format(repo_url, self.github_username))
        g = Github(self.github_username, self.github_password)
        github_user = g.get_user()
        repo = g.get_repo("brainhack101/neurolinks")
        myfork = github_user.create_fork(repo)
        return myfork.ssh_url        

    def pr(self, fork_url, base_url):
        print("Create a pull request from {0} to {1} to finalize publication. This cannot be done automatically.".format(fork_url,base_url))
        
    
def main(args=None):
    
    neurolinks_github_repo_url = "https://github.com/brainhack101/neurolinks"
    neurolinks_dest_path = os.path.join(os.getenv("HOME"),"neurolinks")
    
    def get_neurolinks_default():
        if os.path.isdir(neurolinks_dest_path):
            return neurolinks_dest_path
        return neurolinks_github_repo_url
    
    parser = ArgumentParser("Boutiques publisher", formatter_class=ArgumentDefaultsHelpFormatter, description="A publisher of Boutiques tools in Neurolinks \
(https://brainhack101.github.io/neurolinks). Crawls a Git repository \
for valid Boutiques descriptors and imports them in Neurolinks \
format. Uses your GitHub account to fork the Neurolinks repository and \
commit new tools in it. Requires that your GitHub ssh key is \
configured and usable without password.")
    parser.add_argument("boutiques_repo", action="store",
                        help="Local path to a Git repo containing Boutiques descriptors to publish.")
    parser.add_argument("author_name", action="store",
                        help="Default author name.")
    parser.add_argument("tool_url", action="store",
                        help="Default tool URL.")
    parser.add_argument("--neurolinks-repo", "-n", action="store",
                        default=get_neurolinks_default(),
                        help="Local path to a Git clone of {0}. Remotes: 'origin' should point to a writable fork from which a PR will be initiated; 'base' will be pulled before any update, should point to {0}. If a URL is provided, will attempt to fork it on GitHub and clone it to {1}.".format(neurolinks_github_repo_url, neurolinks_dest_path))
    parser.add_argument("--boutiques-remote", "-r", action="store",
                        default='origin',
                        help="Name of Boutiques Git repo remote used to get URLs of Boutiques descriptor.")
    parser.add_argument("--no-github", action="store_true",
                        help="Do not interact with GitHub at all (useful for tests).")
    parser.add_argument("--github-login", "-u", action="store",
                        help="GitHub login used to fork, clone and PR to {0}. Defaults to value in $HOME/.pygithub. Saved in $HOME/.pygithub if specified.".format(neurolinks_github_repo_url))
    parser.add_argument("--github-password", "-p", action="store",
                        help="GitHub password used to fork, clone and PR to {0}. Defaults to value in $HOME/.pygithub. Saved in $HOME/.pygithub if specified.".format(neurolinks_github_repo_url))
    parser.add_argument("--inter", "-i", action="store_true",
                        default = False,
                        help="Interactive mode. Does not use default values everywhere, checks if URLs are correct or accessible.")
    
    results = parser.parse_args() if args is None else parser.parse_args(args)
    publisher = Publisher(results.boutiques_repo, results.boutiques_remote,
                          results.author_name, results.tool_url, results.inter,
                          results.neurolinks_repo, neurolinks_dest_path,
                          results.github_login, results.github_password, results.no_github).publish()
            
# Execute program
if  __name__ == "__main__":
    main()
