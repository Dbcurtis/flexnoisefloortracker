#!/usr/bin/env python3.8
"""
Tests the local weather module
"""

# import datetime
import unittest
import multiprocessing as mp
from multiprocessing import queues
import time
from collections import deque

import jsonpickle
#import pickle
import context
import localweather
from localweather import MyTime, LocalWeather


def Get_LW(q):
    """Get_LW(q)

    Instantiates, loads and returns a LocalWeather object on the q

    """
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

        _lw2 = LocalWeather()
        _lw2.load_from_other(_lw)
        self.assertEqual(_lw, _lw2)
        self.assertFalse(_lw is _lw2)
        self.assertTrue(_lw2.netstatus is None)
        self.assertEqual(200, _lw.netstatus)

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

            self.assertEqual('Wed Dec  4 16:30:44 2019', _mt.localats)

            self.assertEqual('Thu Dec  5 00:30:44 2019', _mt.utcats)
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
                "[1575506844, 'Thu Dec  5 00:47:24 2019', 'Pacific Standard Time', -8.0]", str(_mtlater.get()))

            a = 0

        except Exception as ex:
            print(str(ex))

    def test02_speed_temp_speed(self):
        """test02_speed_temp_speed()

        Tests if the windspeed and temp works
        """

        temps = localweather.converttemp(233.15)
        self.assertEqual(['233.15K', '-40.00C', '-40.00F'], temps)
        temps = localweather.converttemp(273.15)
        self.assertEqual(['273.15K', '0.00C', '32.00F'], temps)

        speed = localweather.convertspeed(0)
        self.assertEqual([0.0, 0.0], speed)
        speed = localweather.convertspeed(0.44704)
        self.assertAlmostEqual([0.44704, 1.0], speed)
        speed = localweather.convertspeed(1.0)
        self.assertAlmostEqual([1.0, 2.24], speed)
        speed = localweather.convertspeed(-1)
        self.assertAlmostEqual([-1.0, -2.24], speed)
        print('need to test gusts')

    def test03_run_from_Q(self):
        """test03_run_from_Q(

        Tests if the multiprocessing stuff works
        """
        import queue
        ctx = mp.get_context('spawn')
        q = ctx.JoinableQueue(maxsize=5)
       # ps = ctx.Process(target=Get_LW, args=(q,))
        for _ in range(3):  # process can only be started once
            ps = ctx.Process(target=Get_LW, args=(q,))
            ps.start()
            time.sleep(0.0001)

        #[p.start() for p in ps]
        # for i in range(3):  # process can only be started once
            # time.sleep(0.0001)

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

    def test04_lookatObjects(self):
        """test04_lookatObjects(

        if object works
        """
        local_weather_lst = []
        _lw = LocalWeather()
        with open('testlocalWeather60.json', 'r') as fl1:
            try:
                kk = fl1.read()
                local_weather_lst = jsonpickle.decode(
                    kk, classes=(LocalWeather, MyTime,))
                a = 0
            except Exception as ex:
                a = 0
        #deck = deque(local_weather_lst)
        lw1: LocalWeather = local_weather_lst[0]
        #temptupal1 = lw1.get_temp()
        self.assertEqual(['278.03K', '4.88C', '40.78F'], lw1.get_temp()[0])
        self.assertEqual(['275.37K', '2.22C', '36.00F'], lw1.get_temp()[1])
        self.assertEqual(['280.15K', '7.00C', '44.60F'], lw1.get_temp()[2])

        ws = lw1.get_wind()
        self.assertEqual({'dir': '140 degrees', 'speed':
                          [['1.5 m/s', '3.4 mph'], ['0.0 m/s', '0.0 mph']]}, lw1.get_wind())
        a = 0
        self.assertEqual(200, lw1.netstatus)
        self.assertEqual(
            "dict_keys(['base', 'clouds', 'cod', 'coord', 'dt', 'id', 'main', 'name', 'sys', 'timezone', 'visibility', 'weather', 'wind'])", str(lw1.rjson.keys()))

        self.assertEqual(
            'local: Wed Feb 12 19:52:07 2020 Pacific Standard Time', lw1.get_DateTime())

        self.assertEqual('utc: Thu Feb 13 03:52:07 2020',
                         lw1.get_DateTime(local=False))

        a = 0
        # deck = deque(local_weather_lst)


if __name__ == '__main__':
    unittest.main()
