#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
import context
import noisefloor
from smeter import SMeter


class Testnoisefloor(unittest.TestCase):
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

    def test_SMeter(self):
        smeter = SMeter(('ZZSM000;', 5_000_000, ))
        self.assertEquals(
            '[SMeter: freq:5000000, -140.00000dBm, S0]', str(smeter))
        self.assertEquals(
            'SMeter: freq:5000000, -140.00000dBm, S0', repr(smeter))
        a = 0


if __name__ == '__main__':
    unittest.main()
