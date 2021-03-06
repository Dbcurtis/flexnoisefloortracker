#!/usr/bin/env python3.8
"""
Tests the local weather module
"""

# import datetime
# from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque
from typing import Any, Tuple, List, Dict, Set, Callable
import unittest
import multiprocessing as mp
from multiprocessing import queues
from time import sleep as Sleep
import pickle
import context
from noisefloor import Noisefloor
from nfresult import NFResult, NFFactory


class Testnoisefloorresult(unittest.TestCase):
    def setUp(self):
        """setUp()

        """
        pass
        # _ui = UserInput()
        # _ui.request('com4')
        # self.flex = Flex(_ui)
        # self.flex.open()
        # self.flex.do_cmd_list(postproc.INITIALZE_FLEX)

    def tearDown(self):
        """tearDown()

        """
        # self.flex.close()
        pass

    @classmethod
    def setUpClass(cls):
        """setUpClass()

        """
        pass
        # _ui = UserInput()
        # _ui.request('com4')
        # flex = Flex(_ui)
        # flex.open()
        # cls.initial_state = flex.save_current_state()
        # flex.close()
        # postproc.enable_bands(['10', '20'])

    @classmethod
    def tearDownClass(cls):
        """tearDownClass()

        """
        pass
        # _ui = UserInput()
        # _ui.request('com4')
        # flex = Flex(_ui)
        # flex.open()
        # flex.restore_state(cls.initial_state)
        # flex.close()

    def test_01NFResult_inst(self):
        from qdatainfo import NFQ
        from smeteravg import SMeterAvg
        nfr = NFResult()
        self.assertEqual('Not Started', str(nfr))
        self.assertEqual('NFResult: Not Started', repr(nfr))

        nfr1 = NFResult()
        self.assertEqual(nfr, nfr1)

        with open('noisefloordata.pickle', 'rb') as jsi:
            nfqresultlst = list(pickle.load(jsi))

        self.assertEqual(6, len(nfqresultlst))
        nfq: NFQ = nfqresultlst[0]
        nfresult: NFResult = nfq.get()
        nfqnew: NFQ = NFQ(nfresult)

        reads: List[NFResult] = nfq.content.readings
        nfr1.start(strftimein='Apr 11 2020 13:51:10')
        nfr1.end(reads, strftimein='Apr 11 2020 13:51:50')

        # sample: NFResult = NFFactory(oldsample)
        sample = nfr1

        self.assertTrue(sample.completed())
        self.assertEqual(3, len(sample.readings))
        self.assertEqual('Apr 11 2020 13:51:10', sample.starttime)
        self.assertEqual('Apr 11 2020 13:51:50', sample.endtime)
        expres = 'NoiseFloor reading\nApr 11 2020 13:51:10\n    b:40, S6, 1.70\n    b:30, S5, 0.59\n    b:20, S4, 0.42\nApr 11 2020 13:51:50'
        self.assertEqual(expres, str(sample))
        self.assertEqual(sample, sample)

        nfr2 = NFResult()
        nfr2.start(strftimein='Apr 11 2020 13:51:10')
        nfr2.end(sample.readings[:])
        self.assertEqual(sample, nfr2)
        self.assertNotEqual(sample.endtime, nfr2.endtime)

        with open('dadata3hour.pickle', 'rb') as f2:
            try:
                queddata = pickle.load(f2)
            except Exception as ex:
                a = 0
        self.assertEqual(112, len(queddata))
        nflst: List[NFResult] = [
            e.get() for e in queddata if repr(e).startswith('NFQ')]

        nflsttup: List[Tuple[NFResult, NFResult, int]] = []
        for _ in range(1, len(nflst)):
            nflsttup.append((nflst[_ - 1], nflst[_], _,))
        nflstdif: List[Tupal[bool, int]] = [
            (a == b, c,)for a, b, c in nflsttup]

        nfr0: NFResult = nflst[0]
        nfr1: NFResult = nflst[1]
        nfr2: NFResult = nflst[2]
        nfr3: NFResult = nflst[3]

        self.assertTrue(nfr0.__eq__(nfr0))
        self.assertFalse(nfr0.__ne__(nfr0))
        self.assertEqual(nfr0, nfr0)

        self.assertFalse(nfr1 == nfr2)
        self.assertEqual(nfr0, nfr1)
        self.assertTrue(nfr1.__ne__(nfr2))

        self.assertEqual(nflst[13], nflst[14])

        self.assertNotEqual(nflst[32], nflst[33])

        expres = 'NoiseFloor reading\nJul 13 2020 14:47:55\n    b:40, S6, 1.25\n    b:30, S5, 0.46\n    b:20, S3, 0.49\nJul 13 2020 14:49:01'
        self.assertEqual(expres, str(nflst[0]))
        expres = 'NFResult: st:Jul 13 2020 14:47:55, et:Jul 13 2020 14:49:01\nb:40, S6, stddv:1.247, adBm: -86.485, mdBm: -86.485\nb:30, S5, stddv:0.456, adBm: -94.516, mdBm: -94.516\nb:20, S3, stddv:0.492, adBm: -104.083, mdBm: -104.083'
        self.assertEqual(expres, repr(nflst[0]))

        dupsnfrlst: List[Tuple[int, NFResult]] = []
        reducednfrlst: List[NFResult] = nflst[0:1]
        for i in range(1, len(nflst)):
            if nflst[i - 1] != nflst[i]:
                reducednfrlst.append(nflst[i])
            else:
                dupsnfrlst.append((i, nflst[i]))

        self.assertEqual(40, len(reducednfrlst))
        self.assertEqual(20, len(dupsnfrlst))
        self.assertEqual(60, len(nflst))


if __name__ == '__main__':
    unittest.main()
