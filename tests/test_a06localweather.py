#!/usr/bin/env python3.8
"""
Tests the local weather module
"""

# import datetime
import unittest
import multiprocessing as mp
#from multiprocessing import queues
from time import sleep as Sleep
import calendar
#from collections import deque

#import jsonpickle
import pickle
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
            self.assertTrue('UTC:' in strr)
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
        _lw3 = LocalWeather()
        _lw3.load_from_json(_lw.rjson)
        self.assertEqual(_lw, _lw3)
        jslw1 = pickle.dumps(_lw)
        lw4 = pickle.loads(jslw1)
        self.assertEqual(lw4, _lw)
        self.assertEqual(str(lw4), str(_lw))
        self.assertEqual(_lw, lw4)
        lw5 = LocalWeather()
        lw5.load_from_other(_lw)
        self.assertEqual(_lw, lw5)

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

            self.assertEqual('local: 2019/12/04 16:30:44', _mt.localats)

            self.assertEqual('UTC: 2019/12/05 00:30:44', _mt.utcats)
            _dst = MyTime(timestamp=1555000000)

            self.assertTrue(_mt.localtz == 'Pacific Standard Time')
            self.assertEqual(-8.0, _mt.localoffset)
            self.assertTrue(_dst.localtz == 'Pacific Daylight Time')
            self.assertEqual(-7.0, _dst.localoffset)

            self.assertEqual(
                'UTC: 2019/12/05 00:30:44,  Pacific Standard Time: local: 2019/12/04 16:30:44  -8', str(_mt))
            self.assertEqual(
                'UTC: 2019/04/11 16:26:40,  Pacific Daylight Time: local: 2019/04/11 09:26:40  -7', str(_dst))

            mtrep = repr(_mt)
            mtstr = str(_mt)
            self.assertTrue('localweather.MyTime' in mtrep)
            self.assertFalse('localweather.MyTime' in mtstr)
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
                "['UTC: 2019/12/05 00:47:24', 'Pacific Standard Time', -8]", str(_mtlater.get()))

            _mt = MyTime(timestamp=86400)  # one utc day
            self.assertEqual(
                'localweather.MyTime, UTC: 1970/01/02 00:00:00,  Pacific Standard Time: local: 1970/01/01 16:00:00  -8', repr(_mt))

            #sqlts = _mt.get_local_sql_timestamp()
            # self.assertEqual('1970-01-01 16:00:00',
            # _mt.get_local_sql_timestamp())

            _mt = MyTime(timestamp=86400 + 28800)  # start second day pst
            self.assertEqual(
                'localweather.MyTime, UTC: 1970/01/02 08:00:00,  Pacific Standard Time: local: 1970/01/02 00:00:00  -8', repr(_mt))

            # self.assertEqual('1970-01-02 00:00:00',
            # _mt.get_local_sql_timestamp())

        except AssertionError:
            raise
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
            Sleep(0.0001)

        #[p.start() for p in ps]
        # for i in range(3):  # process can only be started once
            # Sleep(0.0001)

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
            self.assertTrue('UTC:' in strr)
            self.assertTrue('Time:' in strr)
        q.join()
        q.close()

    def test04_lookatObjects(self):
        """test04_lookatObjects(

        if object works
        """
        local_weather_lst: LocalWeather = []
        # _lw:LocalWeather = LocalWeather()
        with open('testlocalWeather62.pickle', 'rb') as fl1:
            try:
                local_weather_lst = pickle.load(fl1)
                a = 0
            except Exception as ex:
                a = 0
                raise ex
        #deck = deque(local_weather_lst)
        lw1: LocalWeather = local_weather_lst[0]

        # ftexttemp: str = lw1.get_temp()[0][2]
        temp: float = float(lw1.get_temp()[0][2][:-1])
        self.assertAlmostEqual(67.08, temp, places=2)

        self.assertEquals(
            'local: 2020/04/08 13:57:00 Pacific Daylight Time', lw1.get_DateTime())
        self.assertEquals(
            'UTC: 2020/04/08 20:57:00', lw1.get_DateTime(local=False))
        self.assertEqual(
            "{'temp': 292.64, 'feels_like': 291.39, 'temp_min': 290.15, 'temp_max': 294.26, 'pressure': 1018, 'humidity': 51}", repr(lw1.get_Weather()))

        self.assertEqual(
            "{'speed': [['1.5 m/s', '3.4 mph'], ['0.0 m/s', '0.0 mph']], 'dir': '280 degrees'}", str(lw1.get_wind()))

        self.assertEqual(200, lw1.netstatus)
        keylst = list(lw1.rjson.keys())
        keylst.sort()

        self.assertEqual(
            "['base', 'clouds', 'cod', 'coord', 'dt', 'id', 'main', 'name', 'sys', 'timezone', 'visibility', 'weather', 'wind']", str(keylst))

    def test05_gen_sql(self):
        #from localweather import LocalWeather, MyTime

        local_weather_lst: LocalWeather = []
        # _lw:LocalWeather = LocalWeather()
        with open('testlocalWeather62.pickle', 'rb') as fl1:
            try:
                local_weather_lst = pickle.load(fl1)

            except Exception as ex:
                raise ex
        #deck = deque(local_weather_lst)
        lw1: LocalWeather = local_weather_lst[0]
        a = str(lw1)

        lw2 = LocalWeather()
        lw2.load_from_json(lw1.rjson)
        lw3 = LocalWeather()
        lw3.load_from_other(lw1)

        aaa: List[str] = [
            'INSERT INTO weather SET Sunset = 1586375106000000,',
            'Sunrise = 1586328050000000,',
            'RecDT = 1586354220000000,',
            'Humidity = 51.0, TempF = 67.08, WindS = 3.4, WindD = 280, WindG = 0.0'
        ]
        ans: str = ' '.join(aaa)
        #val: str = lw1.gen_sql()
        self.assertEqual(ans, lw1.gen_sql())


if __name__ == '__main__':
    unittest.main()
