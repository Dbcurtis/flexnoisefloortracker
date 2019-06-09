#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
import context
import deleteme
from deleteme import Deleteme



class Testdeleteme(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def testinstat(self):
        dm = Deleteme()
        self.assertEqual('thing is', str(dm))
        self.assertEqual('Deleteme: thing is', repr(dm))




if __name__ == '__main__':
    unittest.main()
