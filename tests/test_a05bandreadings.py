#!/usr/bin/env python3
"""
Test file for need
"""

# import datetime
import unittest
import jsonpickle
import context
from flex import Flex
from smeter import SMeter
from smeteravg import SMeterAvg
#import smeteravg
#from smeteravg import SMeterAvg
from userinput import UserInput
import bandreadings
from bandreadings import Bandreadings
import postproc


class TestBandreadings(unittest.TestCase):
    """TestBandreadings

    """


    def setUp(self):
        """setUp()

        """
        _ui = UserInput()
        _ui.request('com4')
        self.flex = Flex(_ui)
        self.flex.open()
        self.flex.do_cmd_list(postproc.INITIALZE_FLEX)

    def tearDown(self):
        """tearDown()

        """
        self.flex.close()

    @classmethod
    def setUpClass(cls):
        """setUpClass()

        """
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        cls.initial_state = flex.save_current_state()
        flex.close()

    @classmethod
    def tearDownClass(cls):
        """tearDownClass()

        """
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        flex.restore_state(cls.initial_state)
        flex.close()


    def test01_instat(self):
        """test01_instat()

        """
        _br = Bandreadings([], self.flex, None)
        self.assertEqual('no reading, band 10', str(_br))
        self.assertEqual('Bandreadings: no reading, band 10', repr(_br))
        self.assertEqual('10', _br.bandid)

        _br = Bandreadings([], self.flex, bandid='20')
        self.assertEqual('no reading, band 20', str(_br))
        self.assertEqual('Bandreadings: no reading, band 20', repr(_br))
        self.assertEqual('20', _br.bandid)

        _br = Bandreadings(['14000000', '14200000', '14300000'], self.flex, None)
        self.assertEqual('no reading, band 20', str(_br))
        self.assertEqual('Bandreadings: no reading, band 20', repr(_br))
        self.assertEqual('20', _br.bandid)


    def test02_radioaccess(self):
        """test02_radioaccess()

        """

        try:
            _br = Bandreadings(['14000000', '14074000', '14100000', '14200000'], self.flex)
            _br.get_readings(testing='./quiet20band.json')
            self.assertEqual('[SMeterAvg: -103.45833dBm, S3, var: 0.15720, stddv: 0.39648]',
                             repr(_br.band_signal_strength))

            _br.get_readings(testing='./noisy20band.json')
            self.assertEqual('[SMeterAvg: -102.06250dBm, S4, var: 12.79583, stddv: 3.57713]',
                             repr(_br.band_signal_strength))

            if _br.band_signal_strength.signal_st.get('stddv') > 1.5:
                band = _br.band_signal_strength.band
                tup = _br.band_signal_strength.get_out_of_var()
                sma = _br.changefreqs(tup, band, testing='./focusedbadspotreading.json')
                print(sma)

        except(Exception, KeyboardInterrupt):
            raise

    def test03_changefreqs(self):
        _ui = UserInput()
        try:

            sm = SMeter(('ZZSM098;', 14_100_000))  # s6
            _br = Bandreadings(['14000000', '14100000', '14200000'], self.flex,)  # 14000000
            _br.changefreqs((sm, [],), 20)
            self.fail('test not completed')

        except(Exception, KeyboardInterrupt) as exc:
            self.fail('unexpected exception' + str(exc))

    def test04_cf_process_readings(self):

        file = open('./focusedbadspotreading.json', 'r')
        lines = file.readlines()
        savedreadings = [jsonpickle.decode(i) for i in lines][0]

        #file.close()
        self.fail('test not completed')

if __name__ == '__main__':
    unittest.main()
