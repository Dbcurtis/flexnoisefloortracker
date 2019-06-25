#!/usr/bin/env python3
"""
Test file for need
"""

# import datetime
import unittest
import context
from smeter import SMeter
#import smeteravg
#from smeteravg import SMeterAvg
from userinput import UserInput
import bandreadings
from bandreadings import Bandreadings
import postproc

def initialize_flex(ui):
    """initialize_flex()

    """
    _ui = ui
    results = []
    # for cmd, proc in postproc.INITIALZE_FLEX.items():
    for cmd, proc in postproc.INITIALZE_FLEX.items():
        result = UI.serial_port.docmd(cmd)
        if proc:
            result = proc(result)

        results.append(result)
    return results

class TestBandreadings(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def initialize_flex(cls):
        """initialize_flex()

        """
        _ui = cls.UI
        results = []
        # for cmd, proc in postproc.INITIALZE_FLEX.items():
        for cmd, proc in postproc.INITIALZE_FLEX.items():
            result = _ui.serial_port.docmd(cmd)
            if proc:
                result = proc(result)

            results.append(result)
        return results

    @classmethod
    def setUpClass(cls):
        cls.UI = UserInput()
        cls.UI.request(port='com4')
        cls.UI.open()
        print("com4 Port can be opened")
        cls.initialize_flex()

    @classmethod
    def tearDownClass(cls):
        cls.UI.close()

    def testinstat(self):
        _br = Bandreadings([], None)
        self.assertEqual('no reading, band 10', str(_br))
        self.assertEqual('Bandreadings: no reading, band 10', repr(_br))
        self.assertEqual('10', _br.bandid)

        _br = Bandreadings([], None, bandid='20')
        self.assertEqual('no reading, band 20', str(_br))
        self.assertEqual('Bandreadings: no reading, band 20', repr(_br))
        self.assertEqual('20', _br.bandid)


        _br = Bandreadings(['14000000', '14200000', '14300000'], None)
        self.assertEqual('no reading, band 20', str(_br))
        self.assertEqual('Bandreadings: no reading, band 20', repr(_br))
        self.assertEqual('20', _br.bandid)


    def testradioaccess(self):
        #_ui = UserInput()
        try:
            # aa = ['ZZSM087;', 'ZZSM087;', 'ZZSM087;', 'ZZSM088;', 'ZZSM089;', 'ZZSM088;',
                  # 'ZZSM089;', 'ZZSM089;', 'ZZSM086;', 'ZZSM088;', 'ZZSM088;', 'ZZSM086;']
            #_ui.request('com4')
            #_ui.open()
            #print("com4 Port can be opened")
            _br = Bandreadings(['14000000', '14100000', '14200000'], _ui)
            _br.doit()
            # _ui.close()

        except(Exception, KeyboardInterrupt) as exc:
            # _ui.close()
            self.fail('unexpected exception' + exc.with_traceback())

    def testchangefreqs(self):
        _ui = UserInput()
        try:

            #_ui.request('com4')
            #_ui.open()
#            print("com4 Port can be opened")
            sm = SMeter(('ZZSM098;', 14_100_000))  # s6
            _br = Bandreadings(['14000000', '14100000', '14200000'], _ui)
            _br.changefreqs(sm, 20)
#            _ui.close()

        except(Exception, KeyboardInterrupt) as exc:
#            _ui.close()
            self.fail('unexpected exception' + str(exc))


if __name__ == '__main__':
    unittest.main()
