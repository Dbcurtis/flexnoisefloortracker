#!/usr/bin/env python3.8
"""
Test file for need
"""

# import datetime
import unittest
import multiprocessing as mp
from multiprocessing import queues


import jsonpickle
import context
import localweather
from localweather import MyTime, LocalWeather


def Get_LW(q):
    _lw = LocalWeather()
    _lw.load()
    q.put(_lw)


class TestLocalweather(unittest.TestCase):
    global clsa
    clsa = None
    """TestBandreadings

    """

    def setUp(self):
        """setUp()

        """
        pass

    def tearDown(self):
        """tearDown()

        """
        pass

    @classmethod
    def setUpClass(cls):
        """setUpClass()

        """

        pass

    @classmethod
    def tearDownClass(cls):
        """tearDownClass()

        """
        pass

    def test01a_instat(self):
        """test01a_instat()

        tests if LocalWeather instantiates and loads correctly
        """

        try:

            _lw = LocalWeather()
            self.assertFalse(_lw.valid)

            _lw.load()
            self.assertEqual('std', _lw.units)
            self.assertTrue(_lw.valid)

            strr = str(_lw)
            self.assertTrue('ws:' in strr)
            self.assertTrue('temp:' in strr)
            self.assertTrue('utc:' in strr)
            self.assertTrue('Time:' in strr)

            reprr = repr(_lw)
            self.assertTrue('Localweather: valid:True,' in reprr)

        except Exception as ex:
            print(str(ex))
            self.fail('exception')

    def test01b_instat(self):
        """test01b_instat()

        checks if MyTime instantiates and works

        """

        try:

            _mt = MyTime(timestamp=1575505844)
            self.assertEqual(1575505844, _mt.ts)
            # self.assertEqual('std',_mt.units)
            #self.assertEqual(200, _mt.netstatus)

            _mtz = MyTime(timestamp='1575505844')
            self.assertEqual(1575505844, _mtz.ts)
            self.assertTrue(_mt == _mtz)
            self.assertFalse(_mt is _mtz)
            self.assertTrue(_mt <= _mtz)
            self.assertTrue(_mt >= _mtz)
            self.assertFalse(_mt < _mtz)
            self.assertFalse(_mt > _mtz)

            self.assertEqual('Wed Dec  4 16:30:44 2019', _mt.local)

            self.assertEqual('Thu Dec  5 00:30:44 2019', _mt.utc)
            _dst = MyTime(timestamp=1555000000)

            self.assertTrue(_mt.localtz == 'Pacific Standard Time')
            self.assertEqual(-8.0, _mt.localoffset)
            self.assertTrue(_dst.localtz == 'Pacific Daylight Time')
            self.assertEqual(-7.0, _dst.localoffset)

            self.assertEqual(
                'utc: Thu Dec  5 00:30:44 2019,  Pacific Standard Time: Wed Dec  4 16:30:44 2019  -8.0', str(_mt))
            self.assertEqual(
                'utc: Thu Apr 11 16:26:40 2019,  Pacific Daylight Time: Thu Apr 11 09:26:40 2019  -7.0', str(_dst))

            mtrep = repr(_mt)
            mtstr = str(_mt)
            self.assertTrue('localweather.MyTime,' in mtrep)
            self.assertFalse('localweather.MyTime,' in mtstr)
            self.assertTrue(mtstr in mtrep)

            _mtlater = MyTime(timestamp=1575506844)

            _mtsooner = MyTime(timestamp=1575504844)
            self.assertFalse(_mt == _mtlater)
            self.assertFalse(_mt == _mtsooner)
            self.assertTrue(_mt != _mtlater)
            self.assertTrue(_mt != _mtsooner)
            self.assertTrue(_mt < _mtlater)
            self.assertTrue(_mt > _mtsooner)
            self.assertTrue(_mt <= _mtlater)
            self.assertTrue(_mt >= _mtsooner)
            self.assertFalse(_mt < _mtz)
            self.assertFalse(_mt > _mtz)
            self.assertTrue(_mt <= _mtz)
            self.assertTrue(_mt >= _mtz)
            self.assertFalse(_mt < _mtz)
            self.assertFalse(_mt > _mtz)

            self.assertEqual(
                "(1575506844, 'Thu Dec  5 00:47:24 2019', 'Wed Dec  4 16:47:24 2019', 'Pacific Standard Time', -8.0)", str(_mtlater.get()))

        except Exception as ex:
            print(str(ex))

    def test02_speed_temp_speed(self):
        """test02_speed_temp_speed()

        Tests if the windspeed and temp works
        """

        temps = localweather.converttemp(233.15)
        self.assertEqual(('233.15K', '-40.00C', '-40.00F'), temps)
        temps = localweather.converttemp(273.15)
        self.assertEqual(('273.15K', '0.00C', '32.00F'), temps)

        speed = localweather.convertspeed(0)
        self.assertEqual((0.0, 0.0), speed)
        speed = localweather.convertspeed(0.44704)
        self.assertAlmostEqual((0.44704, 1.0), speed)
        speed = localweather.convertspeed(1.0)
        self.assertAlmostEqual((1.0, 2.24), speed)
        speed = localweather.convertspeed(-1)
        self.assertAlmostEqual((-1.0, -2.24), speed)
        print('need to test gusts')

    def test03_run_from_Q(self):
        """test03_run_from_Q(

        Tests if the multiprocessing stuff works
        """
        import queue
        ctx = mp.get_context('spawn')
        q = ctx.JoinableQueue(maxsize=5)
        ps = [ctx.Process(target=Get_LW, args=(q,))
              for i in range(3)]  # process can only be started once
        [p.start() for p in ps]

        results = []
        try:
            for _ in range(4):
                results.append(q.get(timeout=3))
            self.fail("expected queue.Empty exception did not happen")
        except queue.Empty:
            pass

        self.assertEquals(3, len(results))
        self.assertTrue(q.empty())
        for _lw in results:
            q.task_done()
            self.assertEqual('std', _lw.units)
            self.assertTrue(_lw.valid)

            strr = str(_lw)
            self.assertTrue('ws:' in strr)
            self.assertTrue('temp:' in strr)
            self.assertTrue('utc:' in strr)
            self.assertTrue('Time:' in strr)
        q.join()
        q.close()


if __name__ == '__main__':
    unittest.main()
