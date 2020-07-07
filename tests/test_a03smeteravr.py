#!/usr/bin/env python3
"""
Test file for need
"""

# import datetime
import unittest
import jsonpickle
import datetime
import context
from smeter import SMeter, SMArgkeys
from flex import Flex
#import smeteravg
from smeteravg import SMeterAvg
import userinput
from userinput import UserInput
import postproc


class Testsmeteravg(unittest.TestCase):
    """Testsmeteravg

    """

    def test00_functions(self):
        """test00_functions()

        """
        import smeteravg
        val = None
        try:
            val = smeteravg.get_median(None)
            self.fail('exception 1 not raised')
        except ValueError:
            pass

        try:
            val = smeteravg.get_median([])
            self.fail('exception  not raised')
        except ValueError:
            pass
        val = smeteravg.get_median([1])
        self.assertEqual(1, val)
        self.assertEqual(2, smeteravg.get_median([1, 2, 3]))
        self.assertAlmostEqual(2.5, smeteravg.get_median([1, 2, 3, 4]))

        val = smeteravg.get_median([1.5])
        self.assertAlmostEqual(1.5, val)
        self.assertAlmostEqual(2.5, smeteravg.get_median([1.5, 2.5, 3.5]))
        self.assertAlmostEqual(
            3.0, smeteravg.get_median([1.5, 2.5, 3.5, 4.5]))
        self.assertAlmostEqual(
            3.0, smeteravg.get_median([2.5, 3.5, 1.5, 4.5]))

        lst = [-91.0, -86.0, -89.0, -88.0, -87.0, -86.0, -90.0]
        lstref = lst[:]
        self.assertEqual(lst, lstref)
        self.assertAlmostEqual(-88.0, smeteravg.get_median(lst))
        self.assertNotEqual(lst, lstref)

    def test01_instat(self):
        """test01_instat()

        """
        import smeteravg
        sml = [SMeter(SMArgkeys('ZZSM098;', 14_100_000 + i * 10000))
               for i in range(3)]
        datemarker = datetime.datetime.now().strftime('%Y-%m-%d')
        sma = SMeterAvg(sml, 20)

        self.assertEqual(
            '[b:20, -91.00000adBm, -91.00000mdBm, S6, var: 0.00000, stddv: 0.00000]', str(sma))
        self.assertEqual(
            '[SMeterAvg: b:20, -91.00000adBm, -91.00000mdBm, S6, var: 0.00000, stddv: 0.00000]',
            repr(sma))
        self.assertEqual(20, sma.band)
        self.assertEqual(
            "{'var': 0.0, 'stddv': 0.0, 'sl': 'S6'}", str(sma.signal_st))
        lst = sma.get_start_time_of_readings()
        tt = lst[0][0]
        xx = tt[:10]
        for t in lst:
            self.assertEqual(datemarker, t[0][:10])

        self.assertEqual(-91.0, sma.dBm.get('adBm'))
        self.assertEqual({14100000, 14110000, 14120000}, sma.freqs)
        self.assertEqual(
            '[SMeterAvg: b:20, -91.00000adBm, -91.00000mdBm, S6, var: 0.00000, stddv: 0.00000]',
            repr(sma))
        self.assertEqual(
            '[b:20, -91.00000adBm, -91.00000mdBm, S6, var: 0.00000, stddv: 0.00000]', str(sma))
        # self.assertFalse(sma.noise.get('highnoise'))
        # self.assertFalse(sma.noise.get('lownoise'))
        #self.assertEqual(3, len(sma.noise.get('midnoise')))
        self.assertEqual(-91.0, sma.dBm.get('mdBm'))

        smlf = smeteravg.factory(sml, 20)
        self.assertEqual(
            '[b:20, -91.00000adBm, -91.00000mdBm, S6, var: 0.00000, stddv: 0.00000]', str(smlf))

        def get_readings(testing):
            with open(testing, 'r') as file:
                #file = open(testing, 'r')
                resu = []
                resu = [jsonpickle.decode(_) for _ in file.readlines()]
            # file.close()
            res = resu[0]
            return res
            # newsmaobj = SMeterAvg(res.smlist, res.band)
        oldv1object = get_readings('./quiet20band.json')
        try:
            _ = oldv1object.v
            self.fail('Should be a non-versioned SMeterAvr')
        except Exception as ex:
            a = 0
            pass

        newv1object = smeteravg.factory(oldv1object)
        self.assertAlmostEqual(oldv1object.adBm, newv1object.dBm.get('adBm'))

        # self.assertEqual(
        # '[-91.00000adBm, -91.00000mdBm, S6, var: 0.00000, stddv: 0.00000]', str(newv1object))
        self.assertEqual(3, newv1object.v,
                         'check current version of SMeterAvr')
        _ = 00

    def test02_variances(self):
        """test02_variances()

        """
        sml = [SMeter(
            SMArgkeys(f'ZZSM{98+i*2:03};', 14_100_000 + i * 10000)) for i in range(6)]
        sma = SMeterAvg(sml, 20)
        self.assertEqual(-88.5, sma.dBm.get('adBm'))
        self.assertEqual(-88.5, sma.dBm.get('mdBm'))
        self.assertEqual(20, sma.band)
        self.assertEqual("{'var': 3.5, 'stddv': 1.8708286933869707, 'sl': 'S6'}",
                         str(sma.signal_st))

        #self.assertEqual(1, len(sma.noise.get('highnoise')))
        #self.assertEqual(1, len(sma.noise.get('lownoise')))
        #self.assertEqual(4, len(sma.noise.get('midnoise')))

    def test03_get_sql(self):
        """ttest03_get_sql

        """
        sml = [SMeter(
            SMArgkeys(f'ZZSM{98+i*2:03};', 14_100_000 + i * 10000)) for i in range(6)]
        sma = SMeterAvg(sml, 20)
        self.assertEqual(-88.5, sma.dBm.get('adBm'))
        self.assertEqual(-88.5, sma.dBm.get('mdBm'))
        self.assertEqual(20, sma.band)
        self.assertEqual("{'var': 3.5, 'stddv': 1.8708286933869707, 'sl': 'S6'}",
                         str(sma.signal_st))
        sql: str = sma.gen_sql()
        expl: List[str] = [
            'INSERT INTO bandreadings SET',
            'timedone = 1586436952269148, band = 20,',
            "adBm = -88.5, mdBm = -88.5, sval = 'S6',",
            'stdev = 1.8708286933869707'
        ]
        exp = ' '.join(expl)
        # "INSERT INTO bandreadings SET timedone = 1586436952269148, band = 20, adBm = -88.5, mdBm = -88.5, sval = 'S6', stdev = 1.8708286933869707"
        self.assertTrue('INSERT INTO bandreadings SET timedone = ' in sql)
        self.assertTrue(
            ", band = 20, adBm = -88.5, mdBm = -88.5, sval = 'S6', stdev = 1.8708286933869707" in sql)


if __name__ == '__main__':
    unittest.main()
