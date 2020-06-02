# Contains Boutiques CLI helptext

'''
BOUTIQUES COMMANDS

TOOL CREATION
* create: create a Boutiques descriptor from scratch.
* export: export a descriptor to other formats.
* import: create a descriptor for a BIDS app or update a descriptor from \
an older version of the schema. Options: "bids", "0.4", "cwl", "docopt"
* validate: validate an existing boutiques descriptor.

TOOL USAGE & EXECUTION
* example: generate example command-line for descriptor.
* pprint: generate pretty help text from a descriptor.
* exec: launch or simulate an execution given a descriptor and a set of inputs.
* test: run pytest on a descriptor detailing tests.

TOOL SEARCH & PUBLICATION
* deprecate: deprecate a published tool. The tool will still be published and
usable, but it won't show in search results.
* publish: create an entry in Zenodo for the descriptor and adds the DOI \
created by Zenodo to the descriptor.
* pull: download a descriptor from Zenodo.
* search: search Zenodo for descriptors.

DATA COLLECTION
* data: manage execution data collection.

OTHER
* evaluate: given an invocation and a descriptor,queries execution properties.
* invocation: generate or validate inputs against the invocation schema
* for a given descriptor.
* version: print the Boutiques version.
'''
