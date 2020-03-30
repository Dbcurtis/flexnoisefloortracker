#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
import jsonpickle
from typing import List
from queue import Empty as QEmpty, Full as QFull
import context
from noisefloor import NFResult, Noisefloor
from smeter import SMeter
from smeteravg import SMeterAvg
from userinput import UserInput
from flex import Flex
import postproc

import trackermain
from trackermain import QUEUES as queues
from trackermain import RESET_QS as reset_queues
from trackermain import CTX as ctx
from trackermain import STOP_EVENTS as stopevents


class Testnoisefloor(unittest.TestCase):
    def setUp(self):
        """setUp()

        """
        _ui = UserInput()
        _ui.request('com4')
        self.flex = Flex(_ui)
        self.flex.open()
        self.flex.do_cmd_list(postproc.INITIALZE_FLEX)

    def tearDown(self):
        """tearDown()

        """
        self.flex.close()

    @classmethod
    def setUpClass(cls):
        """setUpClass()

        """
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        cls.initial_state = flex.save_current_state()
        flex.close()
        postproc.enable_bands(['10', '20'])

    @classmethod
    def tearDownClass(cls):
        """tearDownClass()

        """
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        flex.restore_state(cls.initial_state)
        flex.close()

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

        with open('noisefloordata.json', 'r') as jsi:
            nfresultlst = jsonpickle.decode(jsi.readline())

        self.assertEqual(5, len(nfresultlst))
        sample = nfresultlst[0]
        self.assertTrue(sample.completed())
        self.assertEqual(3, len(sample.readings))
        self.assertEqual('Mar 29 2020 17:08:13', sample.starttime)
        self.assertEqual('Mar 29 2020 17:09:18', sample.endtime)
        expres = 'Band Noise Readings\nMar 29 2020 17:08:13\n    b:40, S6, 1.48\n    b:30, S5, 0.53\n    b:20, S4, 0.47\nMar 29 2020 17:09:18\n'
        self.assertEqual(expres, str(sample))
        self.assertEqual(sample, sample)
        self.assertNotEqual(sample, nfresultlst[1])
        nfr1.start()
        nfr1.end(sample.readings[:])
        self.assertEqual(sample, nfr1)
        self.assertNotEqual(sample.endtime, nfr1.endtime)

    def test_02Noisefloor_inst(self):

        dataq = queues['dataQ']
        stope = stopevents['acquireData']

        nf: Noisefloor = Noisefloor(self.flex, dataq, stope, testdata='noisefloordata.json')
        self.assertTrue(nf.open())
        nf.doit(loops=10)

        self.assertTrue(nf.close())
        results: List[NFResult] = []
        try:
            while True:
                results.append(dataq.get(timeout=3))

        except QEmpty:
            pass

        self.assertEqual(5, len(results))
        samp: NFResult = results[2]
        self.assertEqual('Mar 29 2020 17:20:40', samp.starttime)
        self.assertEqual('Mar 29 2020 17:21:45', samp.endtime)
        r0bss: SMeterAvg = samp.readings[0].band_signal_strength
        self.assertEqual('40', r0bss.band)
        self.assertEqual(-104.0, r0bss.dBm['mdBm'])


if __name__ == '__main__':
    unittest.main()
