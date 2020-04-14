#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
#import jsonpickle
import pickle
from typing import List
from queue import Empty as QEmpty, Full as QFull
import context
from noisefloor import NFResult, Noisefloor
from smeter import SMeter
from smeteravg import SMeterAvg
from userinput import UserInput
from flex import Flex
import postproc

from queuesandevents import QUEUES as queues
from queuesandevents import RESET_QS as reset_queues
from queuesandevents import CTX as ctx
from queuesandevents import STOP_EVENTS as stopevents
from queuesandevents import RESET_QS


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

    def test_02Noisefloor_inst(self):

        dataq = queues['dataQ']
        stope = stopevents['acquireData']

        # , testdata='noisefloordata.pickle')
        nf: Noisefloor = Noisefloor(self.flex, dataq, stope)
        self.assertTrue(nf.open())
        nf.doit(loops=10, testdatafile='nfrlistdata.pickle', dups=True)

        self.assertTrue(nf.close())
        results: List[NFResult] = []
        try:
            while True:
                results.append(dataq.get(timeout=3))

        except QEmpty:
            pass

        self.assertEqual(10, len(results))
        samp: NFResult = results[2].get()
        self.assertEqual('Apr 12 2020 23:31:39', samp.starttime)
        self.assertEqual('Apr 12 2020 23:32:43', samp.endtime)
        r0bss: SMeterAvg = samp.readings[0]
        self.assertEqual('40', r0bss.band)
        self.assertEqual(-104.0, r0bss.dBm['mdBm'])

    def test_003Noisefloortestfiles(self):
        from qdatainfo import NFQ
        from math import isclose
        from datetime import datetime as DT
        from datetime import timedelta as TD
        nfqldata: List[NFQ] = []
        with open('nfqlistdata.pickle', 'rb') as jso:
            nfqldata = pickle.load(jso)
        self.assertEqual(90, len(nfqldata))

        nfrldata: List[NFResult] = []
        with open('nfrlistdata.pickle', 'rb') as jso:
            nfrldata = pickle.load(jso)
        self.assertEqual(90, len(nfrldata))

        smavdata: List[SMeterAvg] = []
        with open('smavflistdata.pickle', 'rb') as jso:
            smavdata = pickle.load(jso)
        self.assertEqual(270, len(smavdata))

        nfq = nfqldata[0]
        nfqtimel: List[Tuple[int, TD, DT, DT, ]] = []
        for i in range(1, len(nfqldata)):
            t1: DT = nfqldata[i].utctime
            t0: DT = nfqldata[i - 1].utctime
            td: TD = t1 - t0
            if not isclose(td.total_seconds(), 90.0, abs_tol=0.5):
                nfqtimel.append((i, td, t0, t1,))
        self.assertEqual(6, len(nfqtimel))

        # index, time delta between starts, time taken
        nfrlderr: List[Tuple[int, TD, TD]] = []
        for i in range(1, len(nfrldata)):
            st1: DT = DT.strptime(nfrldata[i].starttime, '%b %d %Y %H:%M:%S')
            st0: DT = DT.strptime(nfrldata[i - 1].starttime, '%b %d %Y %H:%M:%S')
            et: DT = DT.strptime(nfrldata[i].endtime, '%b %d %Y %H:%M:%S')
            sd: TD = st1 - st0
            dur: TD = et - st1
            if not isclose(sd.seconds, 90.0, abs_tol=0.5) or not isclose(dur.seconds, 65.0, abs_tol=3.0):
                nfrlderr.append((i, sd, dur))
        self.assertEqual(6, len(nfrlderr))


if __name__ == '__main__':
    unittest.main()
