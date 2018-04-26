#!/usr/bin/env python

import simplejson
import os.path as op
from jsonschema import validate, ValidationError
from argparse import ArgumentParser
from boutiques import __file__ as bfile


# An exception class specific to creating descriptors.
class CreatorError(ValidationError):
    pass


def createDescriptor(argparser=None, **kwargs):
    boutiquesTemplate = {
        "command-line": "echo [PARAM1] [PARAM2] [FLAG1] > [OUTPUT1]",
        "container-image": {
            "image": kwargs.get("container") or "user/image",
            "type": kwargs.get("container-type") or "singularity",
            "index": kwargs.get("container-index") or "docker://"
        },
        "description": kwargs.get("description") or "tool description",
        "error-codes": [
            {
                "code": kwargs.get("error-code") or 1,
                "description": kwargs.get("error-message") or "Crashed"
            }
        ],
        "groups": [
            {
                "all-or-none": True,
                "mutually-exclusive": False,
                "one-is-required": False,
                "id": "group1",
                "members": [
                    "param1",
                    "flag1"
                ],
                "name": "the param group"
            }
        ],
        "inputs": [
            {
                "id": "param1",
                "name": "The first parameter",
                "optional": True,
                "type": "File", 
                "value-key": "[PARAM1]"
            },
            {
                "id": "param2",
                "name": "The second parameter",
                "optional": False,
                "type": "String", 
                "value-choices": [
                    "mychoice1.log",
                    "mychoice2.log"
                ], 
                "value-key": "[PARAM2]"
            },
            {
                "command-line-flag": "-f",
                "id": "flag1",
                "name": "The first flag",
                "optional": True,
                "type": "Flag",
                "value-key": "[FLAG1]"
            }
        ],
        "name": kwargs.get("name") or "tool name",
        "output-files": [
            {
                "id": "output1",
                "name": "The first output",
                "optional": False,
                "value-key": "[OUTPUT1]",
                "path-template": "[PARAM2].txt",
                "path-template-stripped-extensions": [
                    ".log"
                ]
            }
        ],
        "schema-version": "0.5",
        "suggested-resources": {
            "cpu-cores": 1,
            "ram": 1,
            "walltime-estimate": 60
        },
        "tags": {
            "purpose": "testing",
            "foo": "bar",
            "status": "example"
        },
        "tool-version": "v0.1.0"
    }
    if argparser is None:
        return boutiquesTemplate
    else:
        pass
