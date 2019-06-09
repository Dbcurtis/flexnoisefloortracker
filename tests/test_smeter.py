#!/usr/bin/env python3
"""
Test file for need
"""

import datetime
import unittest
import context
import smeter
from smeter import SMeter


class Testsmeter(unittest.TestCase):
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
        sm = SMeter(('ZZSM000;', 5_000_000))
        self.assertEqual('[SMeter: freq:5000000, -140.00000dBm, S0]', str(sm))
        self.assertEqual('SMeter: freq:5000000, -140.00000dBm, S0', repr(sm))
        self.assertEqual(5_000_000, sm.freq)
        self.assertEqual(-140.00000, sm.signal_st.get('dBm'))
        self.assertEqual('S0', sm.signal_st.get('sl'))
        jj = sm.time
        self.assertEqual(19, len(jj))
        kk = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.assertEqual(kk[0:15], jj[0:15])

        sm = SMeter(('ZZSM098;', 12_123_444))  # s6
        self.assertEqual(12_123_444, sm.freq)
        self.assertEqual(-91.0, sm.signal_st.get('dBm'))
        self.assertEqual('S6', sm.signal_st.get('sl'))

        sm = SMeter(('ZZSM122;', 12_123_456))  # s8
        self.assertEqual(12_123_456, sm.freq)
        self.assertEqual(-79.0, sm.signal_st.get('dBm'))
        self.assertEqual('S8', sm.signal_st.get('sl'))

        sm = SMeter(('ZZSM134;', 12_123_456))  # s9
        self.assertEqual(12_123_456, sm.freq)
        self.assertEqual(-73.0, sm.signal_st.get('dBm'))
        self.assertEqual('S9', sm.signal_st.get('sl'))

        sm = SMeter(('ZZSM174;', 12_123_457))  # s9 + 20
        self.assertEqual(12_123_457, sm.freq)
        self.assertEqual(-53.0, sm.signal_st.get('dBm'))
        self.assertEqual('S9+20', sm.signal_st.get('sl'))

        sm = SMeter(('ZZSM260;', 14_123_456))  # "S9+70"
        self.assertEqual(14_123_456, sm.freq)
        self.assertEqual(-10.0, sm.signal_st.get('dBm'))
        self.assertEqual('S9+60', sm.signal_st.get('sl'))

        # check for smooth transition between from top of s5 to bottom s8
        # abc from 96 to 122
        args = [i for i in range(97, 124)]
        vals = [((i / 2.0) - 140.0, i) for i in args]
        sms = [SMeter(('ZZSM{:03};'.format(i), i * 100000)) for i in args]
        self.assertEqual(27, len(sms))
        self.assertEqual('S5', sms[0].signal_st.get('sl'))
        self.assertEqual('S6', sms[1].signal_st.get('sl'))
        self.assertEqual('S6', sms[12].signal_st.get('sl'))
        self.assertEqual('S7', sms[13].signal_st.get('sl'))
        self.assertEqual('S7', sms[24].signal_st.get('sl'))
        self.assertEqual('S8', sms[25].signal_st.get('sl'))


if __name__ == '__main__':
    unittest.main()
