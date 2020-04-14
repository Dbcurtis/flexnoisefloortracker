#!/usr/bin/env python3.8
"""
Tests the local weather module
"""

from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set
# import datetime
import unittest
#from time import sleep as Sleep
import context
from qdatainfo import *


class Testqdatainfo(unittest.TestCase):
    def setUp(self):
        """setUp()

        """
        pass
        #_ui = UserInput()
        # _ui.request('com4')
        #self.flex = Flex(_ui)
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
        #_ui = UserInput()
        # _ui.request('com4')
        #flex = Flex(_ui)
        # flex.open()
        #cls.initial_state = flex.save_current_state()
        # flex.close()
        #postproc.enable_bands(['10', '20'])

    @classmethod
    def tearDownClass(cls):
        """tearDownClass()

        """
        pass
        #_ui = UserInput()
        # _ui.request('com4')
        #flex = Flex(_ui)
        # flex.open()
        # flex.restore_state(cls.initial_state)
        # flex.close()

    def test_01_inst_Qdatainfo(self):
        qdi: Qdatainfo = None
        try:
            qdi = Qdatainfo()
            self.fail('should have an exception')
        except:
            pass
        qdi = Qdatainfo('string test')
        aa: str = str(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)

        aa = repr(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        self.assertTrue('Qdatainfo: t:', aa)

        qdi = Qdatainfo([{'a': 'alpha', 'b': 'beta'},
                         (1, 2, 3), [1.2, 3.4, 5]])
        aa = repr(qdi)

        self.assertTrue(
            "c: [{'a': 'alpha', 'b': 'beta'}, (1, 2, 3), [1.2, 3.4, 5]]" in aa)
        self.assertTrue('Qdatainfo: t:' in aa)

    def test_02_inst_DataQ(self):

        qdi: DataQ = None
        try:
            qdi = DataQ()
            self.fail('should have an exception')
        except:
            pass

        qdi = DataQ('string test')
        aa: str = str(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        aa = repr(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        self.assertTrue('DataQ: t: ', aa)

    def test_03_inst_LWQ(self):

        qdi: LWQ = None
        try:
            qdi = LWQ()
            self.fail('should have an exception')
        except:
            pass

        qdi = LWQ('string test')
        aa: str = str(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        aa = repr(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        self.assertTrue('LWQ: t: ', aa)

    def test_04_inst_NFQ(self):
        from nfresult import NFResult
        import pickle
        qdi: NFQ = None
        try:
            qdi = NFQ()
            self.fail('should have an exception')
        except:
            pass

        qdi = NFQ('string test')
        aa: str = str(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        aa = repr(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        self.assertTrue('NFQ: t: ', aa)

        testdl: List[NFResult] = None

        with open('noisefloordata.pickle', 'rb') as jsi:
            testdl = pickle.load(jsi)

        testd1 = testdl[0]
        readings: List[SMeterAvg] = testd1.get().readings
        self.assertEqual(3, len(readings))
        reading0: SMeterAvg = readings[0]
        self.assertEqual('40', reading0.band)
        self.assertEqual(
            "{'adBm': -86.85714285714286, 'mdBm': -85.5}",
            str(reading0.dBm))
        self.assertEqual("{'var': 2.892857142857143, 'stddv': 1.7008401285415224, 'sl': 'S6'}",
                         str(reading0.signal_st))

    def test_05_inst_DbQ(self):

        qdi: DbQ = None
        try:
            qdi = DbQ()
            self.fail('should have an exception')
        except:
            pass

        qdi = DbQ('string test')
        aa: str = str(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        aa = repr(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        self.assertTrue('DbQ: t: ', aa)

    def test_06_inst_DbQ(self):

        qdi: DpQ = None
        try:
            qdi = DpQ()
            self.fail('should have an exception')
        except:
            pass

        qdi = DpQ('string test')
        aa: str = str(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        aa = repr(qdi)
        self.assertTrue('t: ' in aa)
        self.assertTrue('c: string test' in aa)
        self.assertTrue('DpQ: t: ', aa)


if __name__ == '__main__':
    unittest.main()
