#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
import context
import dbtools
from dbtools import DBTools


class Testdbtools(unittest.TestCase):
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
        dm = DBTools()
        self.assertEqual('Schema is python1, opened = False, connected = True', str(dm))
        self.assertEqual('DBTools: Schema is python1, opened = False, connected = True', repr(dm))
        dm.close()
        self.assertEqual('DBTools: Schema is python1, opened = False, connected = False', repr(dm))

    def testopen(self):
        dm = DBTools()
        dm.open()
        self.assertEqual('Schema is python1, opened = True, connected = True', str(dm))
        self.assertEqual('DBTools: Schema is python1, opened = True, connected = True', repr(dm))
        dm.close()
        self.assertEqual('Schema is python1, opened = False, connected = False', str(dm))
        self.assertEqual('DBTools: Schema is python1, opened = False, connected = False', repr(dm))


if __name__ == '__main__':
    unittest.main()
