#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import pickle
import unittest
import context
import postproc
from postproc import BandPrams
from postproc import _BAND_DATA, BANDS, enable_bands, _MODE


class Testpostproc(unittest.TestCase):
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

    def test_A001_constants(self):
        self.assertEqual(14, len(_MODE))
        self.assertEquals('LSB', postproc.zzmdpost('00'))
        self.assertEquals('??', postproc.zzmdpost('xxx'))
        self.assertEquals('??', postproc.zzmdpost(None))

    def test_A002_zzifpost(self):
        arg = ('ZZIF000141500000001+00000000000070000000;',
               '000141500000001+00000000000070000000;')
        result = postproc.zzifpost(arg)
        exp = "{'cmd': 'ZZIF', 'freq': '00014150000', 'stepsize': '0001', 'ritF': '+00000', 'rits': '0', 'xits': '0', 'mox': '0', 'mode': 'DIGU'}"
        self.assertEqual(exp, str(result))

    def test_A003_getdata(self):
        dta = postproc.GET_DATA
        dta0 = dta[0]
        self.assertEqual('wait0.5', dta0.cmd)
        self.assertTrue(dta0.fn is None)

        dta1 = dta[1]
        self.assertEqual('ZZSM;', dta1.cmd)
        self.assertEqual('smeter', dta1.fn.__name__)

    def test_A004_getdata(self):
        pass

    def testA005_get_dated_Pickle_filename(self):
        from postproc import DatedFileArg as DFA
        arg: DFA = DFA('pre', 0.5, 'post', 'ext',)
        aa: str = postproc._get_dated_Pickle_filename(arg)
        self.assertEqual('pre_00_30_post.ext', aa)

        arg = DFA('', 0.5, '', '',)
        aa = postproc._get_dated_Pickle_filename(arg)
        self.assertEqual('_00_30_.', aa)

        arg = DFA('', 0.0, '', '',)
        self.assertEqual(
            '_00_00_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', 0.25, '', '',)
        self.assertEqual(
            '_00_15_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', 0.5, '', '',)
        self.assertEqual(
            '_00_30_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', 1, '', '',)
        self.assertEqual(
            '_01_00_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', 0.1666666, '', '',)
        self.assertEqual(
            '_00_10_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', 0.3333333, '', '',)
        self.assertEqual(
            '_00_20_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', 1.3333333, '', '',)
        self.assertEqual(
            '_01_20_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', .1, '', '',)
        self.assertEqual(
            '_00_10_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', .24, '', '',)
        self.assertEqual(
            '_00_15_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', .26, '', '',)
        self.assertEqual(
            '_00_15_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', .4, '', '',)
        self.assertEqual(
            '_00_20_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', .6, '', '',)
        self.assertEqual(
            '_00_40_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', 1.01, '', '',)
        self.assertEqual(
            '_01_00_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', 1.01, '', '',)
        self.assertEqual(
            '_01_00_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', .2, '', '',)
        self.assertEqual(
            '_00_10_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', .34, '', '',)
        self.assertEqual(
            '_00_20_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('', 1.12445, '', '',)
        self.assertEqual(
            '_01_10_.', postproc._get_dated_Pickle_filename(arg))

        arg = DFA('deleteme', 1.12445, 'dm', 'pickle',)
        filename = postproc._get_dated_Pickle_filename(arg)
        testlst = [1, 'one', 2, 'two']
        testlst1 = []

        with open(filename, 'wb') as fl:
            try:
                pickle.dump(testlst, fl)
            except Exception as ex:
                a = 0

        with open(filename, 'rb') as fl:
            try:
                testlst1 = pickle.load(fl)
            except Exception as ex:
                a = 0

        self.assertEqual(testlst, testlst1)

        os.remove(filename)

        a = 0

    def test_B001instat_bandParms(self):

        bdl = list(_BAND_DATA.items())
        it1 = bdl[0]
        bp = BandPrams(it1)
        exp80str = 'band:80, enabled: False, chan: False, [3500000, 3550000, 3600000, 3650000, 3700000, 3750000, 3800000, 3850000, 3900000, 3950000, 4000000]'
        self.assertEqual(exp80str, str(bp))
        exp80str = 'BandPrams: band:80, enabled: False, chan: False, [3500000, 3550000, 3600000, 3650000, 3700000, 3750000, 3800000, 3850000, 3900000, 3950000, 4000000]'
        self.assertEqual(exp80str, repr(bp))
        self.assertEqual('80', bp.bandid)
        cmds: Tuple[str, ...] = bp.get_freq_cmds()
        self.assertEqual(33, len(cmds))
        self.assertEqual('ZZFA00003498500;', cmds[0])
        self.assertEqual('ZZFA00004001500;', cmds[32])
        self.assertFalse(bp.is_enabled())

        it2 = bdl[1]
        bp = BandPrams(it2)
        exp60str = 'band:60, enabled: False, chan: True, [5330500, 5346500, 5357000, 5371500, 5403500]'
        self.assertEqual(exp60str, str(bp))
        exp60str = 'BandPrams: band:60, enabled: False, chan: True, [5330500, 5346500, 5357000, 5371500, 5403500]'
        self.assertEqual(exp60str, repr(bp))
        self.assertEqual('60', bp.bandid)
        cmds: Tuple[str, ...] = bp.get_freq_cmds()
        self.assertEqual(5, len(cmds))
        self.assertEqual('ZZFA00005330500;', cmds[0])
        self.assertEqual('ZZFA00005403500;', cmds[4])
        self.assertFalse(bp.is_enabled())

        self.assertEqual(10, len(BANDS))
        # turn off default bands
        self.assertEqual(3, enable_bands(['40', '20', '30', ], val=False))
        self.assertEqual(
            0, sum([1 for b in BANDS.values() if b.is_enabled()]))
        self.assertEqual(3, enable_bands(['40', '20', '10', ]))
        self.assertEqual(
            3, sum([1 for b in BANDS.values() if b.is_enabled()]))
        self.assertEqual(0, enable_bands(['40', '20', '10', ]))
        # keys need to be string
        self.assertEqual(1, enable_bands(['400', '20', 10, ], val=False))

    # def test_01instat(self):
        #self.assertEqual(10, len(BANDS))

        # dm = DBTools()
        # dm.open()
        # self.assertEqual(
        # 'Schema is python1, opened = True, connected = True', str(dm))
        # self.assertEqual(
        # 'DBTools: Schema is python1, opened = True, connected = True', repr(dm))
        # dm.close()
        # self.assertEqual(
        # 'Schema is python1, opened = False, connected = False', str(dm))
        # self.assertEqual(
        # 'DBTools: Schema is python1, opened = False, connected = False', repr(dm))


if __name__ == '__main__':
    unittest.main()
