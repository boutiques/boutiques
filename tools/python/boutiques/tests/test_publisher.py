from unittest import TestCase
from boutiques.publisher import main
from boutiques import __file__ as bofile
import os

class TestPublisher(TestCase):

    def get_boutiques_dir(self):
        return os.path.join(os.path.split(bofile)[0],"..","..","..")
    
    def test_publisher(self):
         self.assertFalse(main(args=[self.get_boutiques_dir(),
                                     'test author',
                                     'example.com',
                                     '--no-github']))
