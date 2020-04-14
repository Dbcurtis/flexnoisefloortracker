#!/usr/bin/env python3.8
"""
Tests the local weather module
"""

# import datetime
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
        reads: List[NFResult] = nfq.content.readings
        nfr1.start(strftimein='Apr 11 2020 13:51:10')
        nfr1.end(reads, strftimein='Apr 11 2020 13:51:50')

        # sample: NFResult = NFFactory(oldsample)
        sample = nfr1

        self.assertTrue(sample.completed())
        self.assertEqual(3, len(sample.readings))
        self.assertEqual('Apr 11 2020 13:51:10', sample.starttime)
        self.assertEqual('Apr 11 2020 13:51:50', sample.endtime)
        expres = 'NoiseFloor reading\nApr 11 2020 13:51:10\n    b:40, S6, 1.70\n    b:30, S5, 0.59\n    b:20, S4, 0.42\nApr 11 2020 13:51:50\n'
        self.assertEqual(expres, str(sample))
        self.assertEqual(sample, sample)

        nfr2 = NFResult()
        nfr2.start(strftimein='Apr 11 2020 13:51:10')
        nfr2.end(sample.readings[:])
        self.assertEqual(sample, nfr2)
        self.assertNotEqual(sample.endtime, nfr2.endtime)


if __name__ == '__main__':
    unittest.main()
