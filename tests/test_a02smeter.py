#!/usr/bin/env python3
"""
Test file for need
"""

import datetime
import unittest
import random
import context
#import smeter
from smeter import SMeter
import jsonpickle


class Testsmeter(unittest.TestCase):
    """

    """

    def setUp(self):
        """

        """
        pass

    def tearDown(self):
        """

        """
        pass

    @classmethod
    def setUpClass(cls):
        """

        """
        pass

    @classmethod
    def tearDownClass(cls):
        """

        """
        pass

    def testinstat(self):
        """testinstat

        Test class instantiation

        """

        _sm = SMeter(('ZZSM000;', 5_000_000))
        self.assertEqual(
            '[SMeter: freq:5000000, -140.00000dBm, S0]', str(_sm))
        self.assertEqual(
            'SMeter: freq:5000000, -140.00000dBm, S0', repr(_sm))
        self.assertEqual(5_000_000, _sm.freq)
        self.assertEqual(-140.00000, _sm.signal_st.get('dBm'))
        self.assertEqual('S0', _sm.signal_st.get('sl'))
        smytime = _sm.time
        self.assertEqual(19, len(smytime))
        etime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.assertEqual(etime[0:15], smytime[0:15])

        _sm = SMeter(('ZZSM098;', 12_123_444))  # s6
        self.assertEqual(12_123_444, _sm.freq)
        self.assertEqual(-91.0, _sm.signal_st.get('dBm'))
        self.assertEqual('S6', _sm.signal_st.get('sl'))

        _sm = SMeter(['ZZSM122;', 12_123_456])  # s8
        self.assertEqual(12_123_456, _sm.freq)
        self.assertEqual(-79.0, _sm.signal_st.get('dBm'))
        self.assertEqual('S8', _sm.signal_st.get('sl'))

        _sm = SMeter(('ZZSM134;', 12_123_456))  # s9
        self.assertEqual(12_123_456, _sm.freq)
        self.assertEqual(-73.0, _sm.signal_st.get('dBm'))
        self.assertEqual('S9', _sm.signal_st.get('sl'))

        _sm = SMeter(('ZZSM174;', 12_123_457))  # s9 + 20
        self.assertEqual(12_123_457, _sm.freq)
        self.assertEqual(-53.0, _sm.signal_st.get('dBm'))
        self.assertEqual('S9+20', _sm.signal_st.get('sl'))

        _sm = SMeter(('ZZSM260;', 14_123_456))  # "S9+70"
        self.assertEqual(14_123_456, _sm.freq)
        self.assertEqual(-10.0, _sm.signal_st.get('dBm'))
        self.assertEqual('S9+60', _sm.signal_st.get('sl'))

        # check for smooth transition between from top of s5 to bottom s8
        # abc from 96 to 122
        # args = [i for i in range(97, 124)]
        # vals = [((i / 2.0) - 140.0, i) for i in range(97, 124)]
        sms = [SMeter(('ZZSM{:03};'.format(i), i * 100000))
               for i in range(97, 124)]
        self.assertEqual(27, len(sms))
        self.assertEqual('S5', sms[0].signal_st.get('sl'))
        self.assertEqual('S6', sms[1].signal_st.get('sl'))
        self.assertEqual('S6', sms[12].signal_st.get('sl'))
        self.assertEqual('S7', sms[13].signal_st.get('sl'))
        self.assertEqual('S7', sms[24].signal_st.get('sl'))
        self.assertEqual('S8', sms[25].signal_st.get('sl'))

        # check comparisons only need dbm
        _sm1 = SMeter(('ZZSM260;', 14_123_456))  # "S9+70"
        _sm2 = SMeter(('ZZSM260;', 14_123_456))  # "S9+70"
        _sm3 = SMeter(('ZZSM098;', 12_123_444))
        self.assertEqual(_sm1, _sm2)
        self.assertNotEqual(_sm1, _sm3)
        self.assertFalse(_sm1 is _sm2)

        sms1 = sms[:]
        random.shuffle(sms)
        self.assertNotEqual(sms, sms1)
        sms.sort()
        self.assertEqual(sms, sms1)
        for i in range(1, len(sms) - 1):
            self.assertTrue(sms[i] == sms[i])
            self.assertTrue(sms[i - 1] != sms[i])
            self.assertTrue(sms[i - 1] < sms[i])
            self.assertFalse(sms[i - 1] > sms[i])
            self.assertFalse(sms[i] < sms[i])
            self.assertFalse(sms[i] < sms[i - 1])
            self.assertFalse(sms[i] > sms[i])
            self.assertTrue(sms[i] > sms[i - 1])
            self.assertTrue(sms[i - 1] <= sms[i])
            self.assertTrue(sms[i] <= sms[i])
            self.assertFalse(sms[i - 1] >= sms[i])
            self.assertTrue(sms[i] >= sms[i])

            self.assertFalse(sms[i] < sms[i - 1])
            self.assertTrue(sms[i] <= sms[i])

            self.assertTrue(sms[i - 1] < sms[i])
            self.assertFalse(sms[i] < sms[i])
            self.assertFalse(sms[i] < sms[i - 1])
            self.assertTrue(sms[i - 1] <= sms[i])
            self.assertTrue(sms[i] <= sms[i])
            self.assertFalse(sms[i] < sms[i - 1])
            self.assertTrue(sms[i] <= sms[i])

        # check for json output
        _sm = SMeter(('ZZSM098;', 12_123_444))  # s6
        # jsonpickle.set_preferred_backend('json')
        jsonver = jsonpickle.encode(_sm)
        smd = jsonpickle.decode(jsonver)
        self.assertEqual(_sm.time, smd.time)
        self.assertEqual(_sm.signal_st, smd.signal_st)
        self.assertEqual(_sm.freq, smd.freq)


if __name__ == '__main__':
    unittest.main()
