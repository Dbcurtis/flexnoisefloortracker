#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
import context
import noisefloor
from noisefloor import SMeter




class Testnoisefloor(unittest.TestCase):
    def setUp(self):
        a = 0
        pass

    def tearDown(self):
        a = 0
        pass

    @classmethod
    def setUpClass(cls):
        a = 0
        pass

    @classmethod
    def tearDownClass(cls):
        a = 0
        pass

    def test_SMeter(self):
        a = 0
        smeter = SMeter((5_000_000, 'ZZSM000;', ))
        a = str(smeter)
        a = repr(smeter)
        self.assertEquals('', str(smeter))
        self.assertEquals('', repr(smeter))
        a = 0


if __name__ == '__main__':
    unittest.main()
