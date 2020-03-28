#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
import jsonpickle
from typing import List
import context
from noisefloor import NFResult
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

    def test_000SMeter(self):
        smeter = SMeter(('ZZSM000;', 5_000_000, ))
        self.assertEqual(
            '[SMeter: freq:5000000, -140.00000dBm, S0]', str(smeter))
        self.assertEqual(
            'SMeter: freq:5000000, -140.00000dBm, S0', repr(smeter))

    def test_01NFResult_inst(self):
        nfr = NFResult()
        self.assertEqual('Not Started', str(nfr))
        self.assertEqual('Noisefloor: Not Started', repr(nfr))

        nfr1 = NFResult()
        self.assertEqual(nfr, nfr1)
        nfresultlst: List[NFResult] = []
        line: str = None
        with open('banddata.json', 'r') as jsi:
            #nfresultlst = jsonpickle.decode(jsi.readline())
            line = jsi.readline()
        sample = jsonpickle.decode(line)
        sample = nfresultlst[0]
        self.assertTrue(sample.completed())
        self.assertEqual(4, len(sample.readings))
        self.assertEqual('Mar 23 2020 19:09:30', sample.starttime)
        self.assertEqual('Mar 23 2020 19:09:58', sample.endtime)
        expres = 'Band Noise Readings\nMar 23 2020 19:09:30\n    b:80, S4, 0.75\n    b:40, S3, 0.58\n    b:30, S3, 1.32\n    b:20, S2, 0.64\nMar 23 2020 19:09:58\n'
        self.assertEqual(expres, str(sample))
        self.assertEqual(sample, sample)
        self.assertNotEqual(sample, nfresultlst[1])
        nfr1.start()
        nfr1.end(sample.readings[:])
        self.assertEqual(sample, nfr1)
        self.assertNotEqual(sample.endtime, nfr1.endtime)

    def test_02Noisefloor_inst(self):
        pass


if __name__ == '__main__':
    unittest.main()
