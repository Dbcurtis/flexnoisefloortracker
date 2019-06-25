#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import time
import unittest
import context
from userinput import UserInput
from flex import Flex
import postproc


class Testflex(unittest.TestCase):
    def setUp(self):
        a = 0
        pass

    def tearDown(self):
        a = 0
        pass

    @classmethod
    def setUpClass(cls):
        a = 0
        pass

    @classmethod
    def tearDownClass(cls):
        a = 0
        pass

    def testInstantiate(self):
        """
        """
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)

        self.assertEqual('Flex cat: com4, opened: False', str(flex))
        self.assertEqual('[Flex] Flex cat: com4, opened: False', repr(flex))

    def testOpenclose(self):
        """
        """
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        self.assertEqual('Flex cat: com4, opened: True', str(flex))
        self.assertEqual('[Flex] Flex cat: com4, opened: True', repr(flex))

        flex.close()
        self.assertEqual('Flex cat: com4, opened: False', str(flex))
        self.assertEqual('[Flex] Flex cat: com4, opened: False', repr(flex))

        gdata1 = [
            # GET_DATA
            #('wait0.5', None, ),
            ('ZZIF;', None, ),
            # ('wait0.25', None, ),
            #('ZZSM;', smeter, ),
            #('wait0.25', None, ),
            #('ZZSM;', none, ),
            #('wait0.25', None, ),
            #('ZZSM;', smeter, ),

        ]

        flex.open()
        results = flex.get_cat_data(gdata1, 14_000_000)
        self.assertEqual(1, len(results))
        self.assertEqual(41, len(results[0]))
        flex.close()

    def testget_cat_data(self):
        gdata1 = [
            ('wait0.5', None, ),
            ('ZZIF;', postproc.zzifpost, ),
            ]

        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        stim = time.localtime
        results = flex.get_cat_data([], 14_000_000)
        etime = time.localtime

        stim = time.localtime
        results = flex.get_cat_data([('wait0.5', None, ), ], 14_000_000)
        etime = time.localtime

        results = flex.get_cat_data(gdata1, 14_000_000)
        pass


if __name__ == '__main__':
    unittest.main()

