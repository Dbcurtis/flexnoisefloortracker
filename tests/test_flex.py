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
        _ui = UserInput()
        _ui.request('com4')
        self.flex = Flex(_ui)
        self.flex.open()


    def tearDown(self):
        self.flex.close()


    @classmethod
    def setUpClass(cls):
        a = 0
        pass

    @classmethod
    def tearDownClass(cls):
        a = 0
        pass

    def test_instantiate(self):
        """test_instantiate()

        """
        _ui = UserInput()
        _ui.request('com4')
        self.flex = Flex(_ui)

        self.assertEqual('Flex cat: com4, opened: False', str(self.flex))
        self.assertEqual('[Flex] Flex cat: com4, opened: False', repr(self.flex))

    def test_open_close(self):
        """test_open_close()

        """
        #_ui = UserInput()
        #_ui.request('com4')
        #self.flex = Flex(_ui)
        #self.flex.open()
        self.assertEqual('Flex cat: com4, opened: True', str(self.flex))
        self.assertEqual('[Flex] Flex cat: com4, opened: True', repr(self.flex))

        self.flex.close()
        self.assertEqual('Flex cat: com4, opened: False', str(self.flex))
        self.assertEqual('[Flex] Flex cat: com4, opened: False', repr(self.flex))

        #gdata1 = [
            ## GET_DATA
            ##('wait0.5', None, ),
            #('ZZIF;', None, ),
            ## ('wait0.25', None, ),
            ##('ZZSM;', smeter, ),
            ##('wait0.25', None, ),
            ##('ZZSM;', none, ),
            ##('wait0.25', None, ),
            ##('ZZSM;', smeter, ),

        #]

        self.flex.open()
        result = self.flex.do_cmd('ZZIF;')
        self.assertEqual(41, len(result))

    def test_do_cmd(self):
        """test_do_cmd()

        """
        result = self.flex.do_cmd('ZZIF;')

        self.assertEqual(41, len(result))
        result = self.flex.do_cmd('ZZIF')
        self.assertEqual(41, len(result))
        result = self.flex.do_cmd('')
        self.assertEqual('??;', result)
        result = self.flex.do_cmd('junk')
        self.assertEqual('??;', result)

    def test_save_current_state(self):
        """test_save_current_state()

        """
        #_ui = UserInput()
        #_ui.request('com4')
        #self.flex = Flex(_ui)
        #self.flex.open()
        savedstate = self.flex.save_current_state()
        self.assertEqual(savedstate, self.flex.saved_state[:])

        self.flex.restore_saved_state()
        newsavedstate = self.flex.save_current_state()
        self.assertEqual(savedstate, newsavedstate)

        _aa = int([i for i in newsavedstate if 'ZZFA' in i][0][-12:-1])
        _aa = 14000000 if _aa != 14000000 else 15000000
        aat = f'ZZFA{aa:011};'


        self.flex.do_cmd(aat)
        modstate = self.flex.save_current_state()
        self.assertNotEqual(modstate, newsavedstate)

        self.flex.restore_state(newsavedstate)


        a = 0


    def testget_cat_data(self):
        """testget_cat_data()
        """
        gdata1 = [
            ('wait0.5', None, ),
            ('ZZIF;', postproc.zzifpost, ),
            ]

        #_ui = UserInput()
        #_ui.request('com4')
        #self.flex = Flex(_ui)
        #self.flex.open()
        stim = time.localtime
        results = self.flex.get_cat_data([], 14_000_000)
        etime = time.localtime

        stim = time.localtime
        results = self.flex.get_cat_data([('wait0.5', None, ), ], 14_000_000)
        etime = time.localtime

        results = self.flex.get_cat_data(gdata1, 14_000_000)
        pass


if __name__ == '__main__':
    unittest.main()

