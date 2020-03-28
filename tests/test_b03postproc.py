#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
import context
import postproc
from postproc import BandPrams
from postproc import _BAND_DATA, BANDS, enable_bands


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

    def test_001instat(self):

        bdl = list(_BAND_DATA.items())
        it1 = bdl[0]
        bp = BandPrams(it1)
        exp80str = 'band:80, enabled: False, chan: False, [3500000.0, 3550000.0, 3600000.0, 3650000.0, 3700000.0, 3750000.0, 3800000.0, 3850000.0, 3900000.0, 3950000.0, 4000000.0]'
        self.assertEqual(exp80str, str(bp))
        exp80str = 'BandPrams: band:80, enabled: False, chan: False, [3500000.0, 3550000.0, 3600000.0, 3650000.0, 3700000.0, 3750000.0, 3800000.0, 3850000.0, 3900000.0, 3950000.0, 4000000.0]'
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
        self.assertEqual(0, enable_bands(['40', '20', '10', ], val=False))
        self.assertEqual(
            0, sum([1 for b in BANDS.values() if b.is_enabled()]))
        self.assertEqual(3, enable_bands(['40', '20', '10', ]))
        self.assertEqual(
            3, sum([1 for b in BANDS.values() if b.is_enabled()]))
        self.assertEqual(0, enable_bands(['40', '20', '10', ]))
        # keys need to be string
        self.assertEqual(1, enable_bands(['400', '20', 10, ], val=False))

    def test_01instat(self):
        self.assertEqual(10, len(BANDS))

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
