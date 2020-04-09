#!/usr/bin/env python3

"""gets local weather info from openweathermap.org"""
import os
import sys
from typing import List, Sequence, Dict, Mapping, Any, Tuple
from multiprocessing import freeze_support
import logging
import logging.handlers
import requests
#from dbtools import get_bigint_timestamp
#from json.decoder import JSONDecodeError
#import jsonpickle
import pickle
from queue import Empty as QEmpty
import multiprocessing as mp
# import mysql.connector as mariadb
from time import sleep as Sleep
import dbtools
#import pytz

from datetime import datetime as Dtc
from datetime import timezone

from medfordor import Medford_or_Info as MI
#import dbtools


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/localweather'

# stuff needed to access the weather info
OW_DEFAULTKEY = '&appid=a723524c61b7e34a683dfbc79bd683cd'
OW_RVMKEY = '&appid=1320944048cabbe1aebe1fbe9c1c7d6c'
OW_First = 'https://api.openweathermap.org/data/2.5/weather'

PAYLOAD = {'id': str(MI['id']), 'APPID': '1320944048cabbe1aebe1fbe9c1c7d6c'}

#_DT = dbtools.DBTools()
#_DB = _DT.dbase
#_CU = _DT.cursor

_VALID_UNITS = ['std', 'metric', 'imperial']

# jsonpickle.set_preferred_backend('json')  # ('json')
# jsonpickle.set_preferred_backend('json')


def converttemp(k) -> List[str]:
    """converttemp(k)
    k is degrees in Kelven as int, float or str

    returns List [xK, xC, xF]
    """
    result = []
    k1 = 0.0
    try:
        k1 = float(k)
    except ValueError:
        raise ValueError(
            'f(t) is not int, float or text of a float or int number')

    c = k1 - 273.15
    f = (c * (9 / 5)) + 32.0
    result = [f'{k:.2f}K', f'{c:.2f}C', f'{f:.2f}F']
    return result


def convertspeed(msin) -> float:
    """convertspeed(msin)
    msin - meters per seconds as int, float or str

    return list (meters per sec, miles per hour)
    """
    result = []
    ms = float(msin)
    mh = ms * 2.236936
    result = [ms, round(mh, 2)]
    return result


class ComparableMixin(object):
    def _compare(self, other, method):
        try:
            return method(self._cmpkey(), other._cmpkey())
        except (AttributeError, TypeError):
            # _cmpkey not implemented, or return different type,
            # so I can't compare with "other".
            return NotImplemented

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)


class MyTime(ComparableMixin):
    """localweather.MYTime(timestamp=)
    if timestamp not specified uses the timestamp from the local time.

    """

    # timestamp=time.mktime(time.localtime())):
    def __init__(self, timestamp: float = Dtc.now(timezone.utc)):

        self.ts: float = float(timestamp)
        self.utc: Dtc = Dtc.fromtimestamp(self.ts, tz=timezone.utc)
        self.localt: Dtc = self.utc.astimezone()
        self.localats: str = f"local: {self.localt.strftime('%Y/%m/%d %H:%M:%S')}"
        self.utcats: str = f"UTC: {self.utc.strftime('%Y/%m/%d %H:%M:%S')}"
        self.localtz: str = self.localt.tzname()
        _tcs = self.localt.utcoffset()
        self.localoffset: int = int(24 * _tcs.days + _tcs.seconds / 3600)
        a = 0

    def get_local_sql_timestamp_Notneeded(self) -> str:
        """

        YYYY-MM-DD HH:MM:SS

        """

        _fmt: str = '%Y-%m-%d %H:%M:%S'
        result: str = ''

        result = self.localt.strftime(_fmt)

        return result

    def get(self) -> List[Any]:
        """get()

        returns a list of the  the utc and local times, the local time zone, and the local offset
        """
        return [self.utcats, self.localtz, self.localoffset]

    def __str__(self):
        return f'{self.utcats},  {self.localtz}: {self.localats}  {self.localoffset}'

    def __repr__(self):
        return f'localweather.MyTime, {self.utcats},  {self.localtz}: {self.localats}  {self.localoffset}'

    # def __eq__(self, other):
        # return self.ts == other.ts

    # def __ne__(self, other):
        # return self.ts != other.ts

    def __hash__(self):
        return self.ts

    # def __lt__(self, other):
        # return self.ts < other.ts

    # def __le__(self, other):
        # return self.ts <= other.ts

    # def __gt__(self, other):
        # return self.ts > other.ts

    # def __ge__(self, other):
        # return self.ts >= other.ts
    def _cmpkey(self):
        return self.ts

    def get_local_time(self) -> Dtc:
        return self.localt

    def get_utc_time(self) -> Dtc:
        return self.utc


def different(arg1: Any, arg2: Any) -> bool:
    """different(other)

    """

    result = False
    if isinstance(arg2, LocalWeather) and isinstance(arg1, LocalWeather):
        o: LocalWeather = arg2
        mains = arg1.rjson['main']
        omains = arg2.rjson['main']
        return arg1.times['sunup'] != o.times['sunup'] or \
            arg1.times['sunset'] != o.times['sunset'] or \
            mains['temp'] != omains['temp'] or \
            mains['temp_min'] != omains['temp_min'] or \
            mains['temp_max'] != omains['temp_max'] or \
            arg1.rjson['wind'] != o.rjson['wind']

    return result


_SQL_COLUMN_NAMES_LIST: List[str] = [
    'WRECID',
    'timerecid',
    'RecDT',
    'Sunset',
    'Sunrise',
    'Humidity',
    'TempF',
    'WindS',
    'WindD',
    'WindG',
]


class LocalWeather(ComparableMixin):
    """ LocalWeather()


    """
    valid = False
    rjson = {}
    units = 'std'
    netstatus = []
    maint = {}
    version = '00.00.01'

    def __init__(self):
        """LocalWeather()


        """
        self.valid = False
        self.rjson = {}
        self.units = 'std'
        self.netstatus = None

    # def __eq__(self, other):
        # pass

    # def __ne__(self, other):
        # pass

    def _cmpkey(self):
        return self.times['dt'].get()[0]

    def __hash__(self):
        return self.times['dt'].get()[0]

    def __str__(self):
        if not self.valid:
            return 'invalid'

        mm = self.maint
        clk = self.times['dt']
        t = mm['temp'][0]
        wnd = self.maint['wind']
        wsp = wnd['speed']
        # --------------------------------
        result = f'ws:{wsp[0]}, g:{wsp[1]}; temp:{t[1]}, {t[2]};  {str(clk)}'
        return result

    def __repr__(self):
        result = str(self)
        return f'Localweather: valid:{self.valid}, {result}'

    def gen_sql(self) -> str:
        # weather fields
        # WRECID
        # timerecid
        # RecDT
        # Sunset
        # Sunrise
        # Humidity
        # TempF
        # WindS
        # WindD
        # WindG

        mm = self.maint

        tempf = mm['temp'][0][2][:-1].strip()
        wnd = mm['wind']
        wnds = wnd['speed'][0][1][:-3].strip()
        wdir = wnd['dir'][:-8].strip()
        wgust = wnd['speed'][1][1][:-3].strip()
        hum = mm['humidity'][:-1].strip()

        #sss = dbtools.get_bigint_timestamp(self.times['dt'])
        trecdt: int = dbtools.get_bigint_timestamp(self.times['dt'])
        tsup: int = dbtools.get_bigint_timestamp(self.times['sunup'])
        tsdn: int = dbtools.get_bigint_timestamp(self.times['sunset'])

        times = f"Sunset = {tsdn}, Sunrise = {tsup}, RecDT = {trecdt}"
        wind = f"WindS = {wnds}, WindD = {wdir}, WindG = {wgust}"
        htemp = f"Humidity = {hum}, TempF = {tempf}"

        result: str = f'INSERT INTO weather SET {times}, {wind}, {htemp}'
        return result

    def has_changed(self, other):
        result = False
        if isinstance(other, LocalWeather):
            o = other
            omains = other.rjson['main']
            smains = self.rjson['main']
            return self.times['sunup'] != o.times['sunup'] or \
                self.times['sunset'] != o.times['sunset'] or \
                smains['temp'] != omains['temp'] or \
                smains['temp_min'] != omains['temp_min'] or \
                smains['temp_max'] != omains['temp_max'] or \
                self.rjson['wind'] != o.rjson['wind']

        return result

    def load_from_other(self, other):
        if not isinstance(other, LocalWeather):
            raise ValueError('other must be a LocalWeather object')
        self.load_from_json(other.rjson)

    def load_from_json(self, js: str):
        """_load_from_json(js)

        Note that netstatus does not get copied over and is None

        """
        self.valid = True
        self.rjson: str = js
        jsys = self.rjson['sys']

        self.times = {'dt': MyTime(self.rjson['dt']),
                      'sunup': MyTime(jsys['sunrise']),
                      'sunset': MyTime(jsys['sunset'])}
        mains = self.rjson['main']
        hum = float(mains['humidity'])
        wind = self.rjson['wind']
        speed = wind['speed']
        try:
            gust = wind['gust']
        except:
            gust = 0

        degree = -11.0
        try:
            degree = round(float(wind['deg']), 0)
        except KeyError as ke:
            pass

        rspeed = convertspeed(speed)
        rgust = convertspeed(gust)

        self.maint = {'temp': (converttemp(mains['temp']), converttemp(mains['temp_min']), converttemp(mains['temp_max'])),
                      'humidity': f'{hum:.1f}%',
                      'wind': {'speed': [[f'{rspeed[0]:.1f} m/s', f'{rspeed[1]:.1f} mph'], [f'{rgust[0]:.1f} m/s', f'{rgust[1]:.1f} mph']], 'dir': f'{degree:.0f} degrees'},
                      'times': {'acquire': self.times['dt'].localats, 'sunup': self.times['sunup'].localats, 'sunset': self.times['sunset'].localats, }
                      }

    def load(self):
        """lw.load()


        gets the local weather for Medford OR.
        Leaves the result in the lw.maint dict

        """

        request_status = requests.get(OW_First, params=PAYLOAD)
        self.netstatus = request_status.status_code
        if not request_status.status_code == 200:
            raise Exception(f'{r.url} returned {r.status_code}')

        try:
            self.rjson = request_status.json()
            self.load_from_json(self.rjson)

        except Exception as e:
            print(request_status)
            print(e)

    def get_DateTime(self, local=True):
        if local:
            return f'{self.times["dt"].localats} {self.times["dt"].localtz}'

        return f'{self.times["dt"].utcats}'

    def get_Weather(self) -> Dict[str, Any]:
        return self.rjson['main']

    def get_wind(self, local=True):
        return self.maint['wind']

    def get_temp(self):
        """get_temp()

        Gets a tuple of current temp, min temp and max temp,
        each of which is a tuple of (kelven, centegrade, ferenhite ) all text
        """
        return self.maint['temp']


def main():
    from trackermain import CTX, QUEUES

    que = QUEUES['dataQ']

    saved: List[LocalWeather] = []
    numreadings = 10
    fn: str = 'testlocalWeather62.pickle'
    delaymin = 7
    if True:
        for i in range(numreadings):
            _lw = LocalWeather()
            _lw.load()
            saved.append(_lw)
            print('.', end='')
            if i >= numreadings - 1:
                continue
            for _ in range(4 * delaymin):
                Sleep(15)

        with open(fn, 'wb') as fl:

            try:
                pickle.dump(saved, fl)
            except Exception as ex:
                a = 0

        restored: List[LocalWeather] = None
        with open(fn, 'rb') as fl:
            try:
                restored = pickle.load(fl)
            except Exception as ex:
                a = 0

        if restored[0] != saved[0]:
            print ('saved and restored first entry are not equal')

    with open(fn, 'rb') as fl:
        try:
            saved = pickle.load(fl)
        except Exception as ex:
            a = 0

    for v in saved:
        que.put(v)

    restoredq = []
    running = True
    while running:
        try:
            val = que.get(True, 0.01)
            restoredq.append(val)
            que.task_done()
        except Exception:
            running = False

    if restoredq[0] != saved[0]:
        print ('saved and restoredq first entry are not equal')

    print ('all done')


if __name__ == '__main__':

    freeze_support()
    from localweather import LocalWeather
    import datetime
    from datetime import timezone
    from time import sleep as Sleep
    if not os.path.isdir(LOG_DIR):
        os.mkdir(LOG_DIR)

    LF_HANDLER = logging.handlers.RotatingFileHandler(
        ''.join([LOG_DIR, LOG_FILE, ]),
        maxBytes=10000,
        backupCount=5,
    )
    LF_HANDLER.setLevel(logging.INFO)
    LC_HANDLER = logging.StreamHandler()
    LC_HANDLER.setLevel(logging.INFO)  # (logging.ERROR)
    LF_FORMATTER = logging.Formatter(
        '%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
    LC_FORMATTER = logging.Formatter(
        '%(name)s: %(levelname)s - %(message)s')
    LC_HANDLER.setFormatter(LC_FORMATTER)
    LF_HANDLER.setFormatter(LF_FORMATTER)
    THE_LOGGER = logging.getLogger()
    THE_LOGGER.setLevel(logging.INFO)
    THE_LOGGER.addHandler(LF_HANDLER)
    THE_LOGGER.addHandler(LC_HANDLER)
    THE_LOGGER.info('localweather executed as main')
    # LOGGER.setLevel(logging.DEBUG)

    try:
        main()

    except(Exception, KeyboardInterrupt) as exc:
        sys.exit(str(exc))

    finally:
        sys.exit('normal exit')


