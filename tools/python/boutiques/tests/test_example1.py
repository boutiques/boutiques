#!/usr/bin/env python

import os, subprocess
from unittest import TestCase
from boutiques import __file__ as bofile
from boutiques.localExec import main

class TestExample1(TestCase):

    def get_boutiques_dir(self):
        return os.path.split(bofile)[0]
    
    def get_examples_dir(self):
        return os.path.join(os.path.dirname(__file__),
                            "..","schema","examples")
                
    def test_example1_no_exec(self):
        example1_dir = os.path.join(self.get_examples_dir(),"example1")       
        self.assertFalse(main(args=['-i',
                                    os.path.join(example1_dir,"invocation.json"),
                                    os.path.join(example1_dir,"example1.json")]))

    def test_example1_exec(self):
        example1_dir = os.path.join(self.get_examples_dir(),"example1")       
        self.assertFalse(main(args=['-i',
                                    os.path.join(example1_dir,"invocation.json"),
                                    os.path.join(example1_dir,"example1.json"),
                                    '-e','-d']))

    def test_example1_no_exec_random(self):
        example1_dir = os.path.join(self.get_examples_dir(),"example1")       
        self.assertFalse(main(args=[os.path.join(example1_dir,"example1.json"),
                                    '-r', '-n' '10']))
