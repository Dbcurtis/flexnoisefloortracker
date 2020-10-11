#!/usr/bin/env python3

"""gets local weather info from openweathermap.org
   see: https://openweathermap.org/current
"""

import qdatainfo
import os
import sys
from typing import Any, List, Dict, Tuple
#from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque, Iterable
from multiprocessing import freeze_support
import logging
import logging.handlers
import requests
import pickle
from datetime import datetime as Dtc
from datetime import timezone
from collections import namedtuple

#from queue import Empty as QEmpty
import multiprocessing as mp
from time import sleep as Sleep
#import qdatainfo
import dbtools
import timestampaux
from medfordor import Medford_or_Info as MI
from queuesandevents import QUEUE_KEYS as QK


LOGGER = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/localweather'

# stuff needed to access the weather info
#OW_DEFAULTKEY = '&appid=a723524c61b7e34a683dfbc79bd683cd'
#OW_RVMKEY = '&appid=1320944048cabbe1aebe1fbe9c1c7d6c'
OW_First = 'https://api.openweathermap.org/data/2.5/weather'
PAYLOAD = {'id': str(MI['id']), 'APPID': '1320944048cabbe1aebe1fbe9c1c7d6c'}
_VALID_UNITS = ['std', 'metric', 'imperial']

TempTuple = namedtuple('TempTuple', ['k', 'c', 'f'])
TempTupleStr = namedtuple('TempTupleStr', ['k', 'c', 'f'])
SpeedTuple = namedtuple('SpeedTuple', ['mps', 'mph'])


def converttemp(kin: Any) -> Tuple[float, float, float]:
    """converttemp(k)
    k is degrees in Kelven as int, float or str

    returns TempTuple [xK, xC, xF]
    """
    result: TempTuple = TempTuple(0, 0, 0)
    _k1: float = 0.0
    try:
        _k1 = float(kin)
    except ValueError:
        raise ValueError(
            'f(t) is not int, float or text of a float or int number')

    _c1: float = _k1 - 273.15
    _f1: float = (_c1 * (9 / 5)) + 32.0
    #result = TempTuple(f'{_k1:.2f}K', f'{_c1:.2f}C', f'{_f1:.2f}F')
    result = TempTuple(_k1, _c1, _f1)
    return result


def temp2str(tt: TempTuple) -> TempTupleStr:
    result = TempTupleStr(f'{tt.k:.2f}K', f'{tt.c:.2f}C', f'{tt.f:.2f}F')
    return result


def convertspeed(msin) -> Tuple[float, float]:
    """convertspeed(msin)
    msin - meters per seconds as int, float or str

    return SpeedTuple (meters per sec, miles per hour)
    """
    result = SpeedTuple(-1.1, -1.1)
    _ms: float = float(msin)
    _mh: float = _ms * 2.236936
    result: SpeedTuple = SpeedTuple(_ms, round(_mh, 2))
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

        returns a list of strings for  the utc and local times, the local time zone, and the local offset
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
    version = '00.00.02'

    def __init__(self):
        """LocalWeather()


        """
        self.valid = False
        self.rjson = {}
        self.units = 'std'
        self.netstatus = None
        self.times = None

    # def __eq__(self, other):
        # pass

    # def __ne__(self, other):
        # pass

    def _cmpkey(self):
        return self.times['dt'].ts
        # return self.times['dt'].get()[0]

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
        """gen_sql()

        TBD
        """

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

        tempf = f'{round(mm["temp"][0].f) :1d}'  # mm['temp'][0].f
        wnd = mm['wind']
        wnds = wnd['speed'][0][1][:-3].strip()
        wdir = wnd['dir'][:-8].strip()
        wgust = wnd['speed'][1][1][:-3].strip()
        hum = mm['humidity'][:-1].strip()

        #sss = dbtools.get_bigint_timestamp(self.times['dt'])
        trecdt: int = timestampaux.get_bigint_timestamp(self.times['dt'])
        tsup: int = timestampaux.get_bigint_timestamp(self.times['sunup'])
        tsdn: int = timestampaux.get_bigint_timestamp(self.times['sunset'])

        times = f"Sunset = {tsdn}, Sunrise = {tsup}, RecDT = {trecdt}"
        wind = f"WindS = {wnds}, WindD = {wdir}, WindG = {wgust}"
        htemp = f"Humidity = {hum}, TempF = {tempf}"

        result: str = f'INSERT INTO weather SET {times}, {htemp}, {wind}'
        return result

    def has_changed(self, other: Any) -> bool:
        """has_changed(other)

        checks if the weather parameters are different, not related to the time the data was collected
        which would be (Not equals)

        """
        result = False
        if isinstance(other, LocalWeather):
            o: LocalWeather = other
            omains = other.rjson['main']
            smains = self.rjson['main']
            return self.times['sunup'] != o.times['sunup'] or \
                self.times['sunset'] != o.times['sunset'] or \
                smains['temp'] != omains['temp'] or \
                smains['temp_min'] != omains['temp_min'] or \
                smains['temp_max'] != omains['temp_max'] or \
                self.rjson['wind'] != o.rjson['wind']

        return result

    # TODO should be deprecated and replaced by localweather.factory
    def load_from_other(self, other: Any):
        """load_from_other(other)

        """
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
        except KeyError:
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


def different(arg1: LocalWeather, arg2: LocalWeather) -> bool:
    """different(arg1: LocalWeather, arg2: LocalWeather) -> bool:

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


def factory(lwin: LocalWeather) -> LocalWeather:
    """factory(lwin: LocalWeather) -> LocalWeather

    """
    result = LocalWeather()
    result.load_from_json(lwin.rjson)
    return result


def main():
    from trackermain import CTX, QUEUES
    from qdatainfo import LWQ

    que = QUEUES[QK.dQ]

    saved: List[LocalWeather] = []
    numreadings = 10
    fn: str = 'testlocalWeather62.pickle'
    delaymin = 7
    if False:
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
            except Exception:  # as ex:
                pass

        restored: List[LocalWeather] = None
        with open(fn, 'rb') as fl:
            try:
                restored = pickle.load(fl)
            except Exception:
                pass

        if restored[0] != saved[0]:
            print('saved and restored first entry are not equal')

    with open(f'./tests/{fn}', 'rb') as fl:
        try:
            saved = pickle.load(fl)
        except Exception:
            pass

    for v in saved:
        qv: LWQ = LWQ(v)
        que.put(qv)

    restoredq: List[LocalWeather] = []
    running = True
    while running:
        try:
            qval: LWQ = que.get(True, 0.01)
            restoredq.append(qval.get())
            que.task_done()
        except Exception:
            running = False

    if restoredq[0] != saved[0]:
        print('saved and restoredq first entry are not equal')

    print('all done')


if __name__ == '__main__':

    freeze_support()
    from datetime import timezone

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

    THE_LOGGER.addHandler(LF_HANDLER)
    THE_LOGGER.addHandler(LC_HANDLER)

    # THE_LOGGER.setLevel(logging.CRITICAL)
    # THE_LOGGER.setLevel(logging.ERROR)
    # THE_LOGGER.setLevel(logging.WARNING)
    THE_LOGGER.setLevel(logging.INFO)
    # LOGGER.setLevel(logging.DEBUG)
    # THE_LOGGER.setLevel(logging.NOTSET)
    THE_LOGGER.info('localweather executed as main')

    try:
        main()

    except(Exception, KeyboardInterrupt) as exc:
        sys.exit(str(exc))

    finally:
        sys.exit('normal exit')


