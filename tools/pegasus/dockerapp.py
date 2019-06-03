#!/usr/bin/env python

import simplejson as json
import os
import stat
from Pegasus.DAX3 import ADAG, Job, File, Link

class DockerApp(object):

	def __init__(self, appfile, map, transfer=False):
		self.data = json.load(open(appfile))
		self.map = map
		self.transfer = transfer
		if not os.path.exists("wrappers"):
			os.mkdir("wrappers")


	def generate_job(self):
		job = Job(self.data["name"], node_label=self.data["name"])
		
		# Outputs parsing
		for output in self.data["outputs"]:
			if output["command-line-key"]:
				if "value-template" in output and output["value-template"]:
					self.data["command-line"] = self.data["command-line"].replace(output["command-line-key"], output["value-template"])
				else:
					self.data["command-line"] = self.data["command-line"].replace(output["command-line-key"], self.map[output["name"]])
					if output["type"] == "File":
						job.uses(self.map[output["name"]], link=Link.OUTPUT, transfer=self.transfer)

		# Inputs parsing
		inputsMap = {}
		for input in self.data["inputs"]:
			if input["command-line-key"]:
				self.data["command-line"] = self.data["command-line"].replace(input["command-line-key"], self.map[input["name"]])
				inputsMap[input["command-line-key"]] = self.map[input["name"]]
			if input["type"] == "File":
				job.uses(self.map[input["name"]], link=Link.INPUT)

		# Outputs value-template parsing
		for output in self.data["outputs"]:
			if "value-template" in output and output["value-template"]:
				for input in inputsMap:
					if input in output["value-template"]:
						value = output["value-template"].replace(input, inputsMap[input])
						job.uses(value, link=Link.OUTPUT, transfer=self.transfer)
						break

		self.create_wrapper()

		return job


	def create_wrapper(self):
		f = open("wrappers/%s" % self.data["name"], "w")
		f.write("#!/bin/bash\n")
		f.write("PWD=`pwd`\n")
		f.write("docker run -v $PWD:/scratch -w=/scratch -t %s %s\n" % (self.data["docker-image"], self.data["command-line"]))
		f.close()
		st = os.stat("wrappers/%s" % self.data["name"])
		os.chmod("wrappers/%s" % self.data["name"], st.st_mode | stat.S_IEXEC)
