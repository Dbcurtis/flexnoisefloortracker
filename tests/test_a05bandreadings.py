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
            self.assertEqual(
                '[SMeterAvg: -103.45833adBm, -103.50000mdBm, S3, var: 0.15720, stddv: 0.39648]',
                repr(_br.band_signal_strength))

            _br.get_readings(testing='./noisy20band.json')
            self.assertEqual(
                '[SMeterAvg: -102.06250adBm, -103.50000mdBm, S3, var: 12.79583, stddv: 3.57713]',
                repr(_br.band_signal_strength))

            #if _br.band_signal_strength.signal_st.get('stddv') > 1.5:
                #_br.changefreqs(
                    #testing='./focusedbadspotreading.json')
            #self.assertEqual(
                #'[SMeterAvg: -103.32090adBm, -103.50000mdBm, S3, var: 0.74774, stddv: 0.86472]',
                #repr(_br.band_signal_strength))


        except(Exception, KeyboardInterrupt) as exc:
            self.fail('unexpected exception' + str(exc))


    def test03_get_readings(self):
        """test03_get_readings()

        """
        _br = Bandreadings(['14000000', '14100000', '14200000'], self.flex,)  # 14000000
        _br.get_readings(testing='./noisy20band.json')
        smar = _br.band_signal_strength
        self.assertEqual(16, len(smar.smlist))
        self.assertEqual('SMeter: freq:14000000, -105.00000dBm, S3', repr(smar.smlist[0]))
        self.assertEqual('SMeter: freq:14074000, -96.00000dBm, S5', repr(smar.smlist[6]))
        self.assertEqual(
            '[SMeterAvg: -102.06250adBm, -103.50000mdBm, S3, var: 12.79583, stddv: 3.57713]',
            repr(smar))


    def test07_changefreqs(self):
        """test07_changefreqs()

        """
        _br = Bandreadings(['14000000', '14074000', '14100000', '14200000'], self.flex,)  # 14000000
        _br.get_readings(testing='./noisy20band.json')
        sma = _br.band_signal_strength
        sml = sma.smlist[:]



        a = 0


        file = open('./focusedbadspotreading.json', 'r')
        lines = file.readlines()
        savedreadings = [jsonpickle.decode(i) for i in lines][0]

        # file.close()
        self.fail('test not completed')


        _ui = UserInput()
        try:

            sm = SMeter(('ZZSM098;', 14_100_000))  # s6
            _br = Bandreadings(['14000000', '14100000', '14200000'], self.flex,)  # 14000000
            _br.get_readings(testing='./noisy20band.json')
            _br.changefreqs(testing='./focusedbadspotreading.json')
            self.fail('test not completed')


        except(Exception, KeyboardInterrupt) as exc:
            self.fail('unexpected exception' + str(exc))

    def test04_cf_process_readings(self):
        """test04_cf_process_readings()

        """
        _br = Bandreadings(['14000000', '14074000', '14100000', '14200000'], self.flex,)  # 14000000
        _br.get_readings(testing='./quiet20band.json')
        self.assertFalse(_br.cf_process_readings())
        # oldsmalst = [_br.band_signal_strength][:]
        _br = Bandreadings(['14000000', '14074000', '14100000', '14200000'], self.flex,)  # 14000000

      #  need to figure out what was the noisy frequency when you removed the damn things
        _br.get_readings(testing='./noisy20band.json')
        temp_smeteravg = _br.cf_process_readings()
        self.assertTrue(temp_smeteravg)
        self.assertEqual(
            '[SMeterAvg: -104.04167adBm, -104.00000mdBm, S3, var: 0.33902, stddv: 0.58225]',
            repr(temp_smeteravg))
        self.assertTrue(_br.single_noise_freq)
        self.dropped_freqs[0]


if __name__ == '__main__':
    unittest.main()
