#!/usr/bin/env python3

"""gets local weather info from openweathermap.org"""
import os
import sys
from multiprocessing import freeze_support
import logging
import logging.handlers
import requests
#from json.decoder import JSONDecodeError
import jsonpickle
# import pickle
# import mysql.connector as mariadb
import time
from medfordor import Medford_or_Info as MI
import dbtools


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/localweather'

# stuff needed to access the weather info
OW_DEFAULTKEY = '&appid=a723524c61b7e34a683dfbc79bd683cd'
OW_RVMKEY = '&appid=1320944048cabbe1aebe1fbe9c1c7d6c'
OW_First = 'https://api.openweathermap.org/data/2.5/weather'

PAYLOAD = {'id': str(MI['id']), 'APPID': '1320944048cabbe1aebe1fbe9c1c7d6c'}

_DT = dbtools.DBTools()
_DB = _DT.dbase
_CU = _DT.cursor

_VALID_UNITS = ['std', 'metric', 'imperial']

# jsonpickle.set_preferred_backend('json')  # ('json')
# jsonpickle.set_preferred_backend('json')


def converttemp(k):
    """converttemp(k)
    k is degrees in Kelven

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


def convertspeed(msin):
    """convertspeed(msin)
    msin - meters per seconds

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

    def __init__(self, timestamp=time.mktime(time.localtime())):
        self.ts = int(timestamp)
        localts = time.localtime(self.ts)
        self.localats = time.asctime(localts)
        self.utcats = time.asctime(time.gmtime(self.ts))
        self.localtz = localts.tm_zone
        self.localoffset = localts.tm_gmtoff / 3600  # 60*60

    def get(self):
        """get()

        returns a list of the timestamp, the utc and local times, the local time zone, and the local offset
        """
        return [self.ts, self.utcats, self.localtz, self.localoffset]

    def __str__(self):
        return f'utc: {self.utcats},  {self.localtz}: {self.localats}  {self.localoffset}'

    def __repr__(self):
        return f'localweather.MyTime, utc: {self.utcats},  {self.localtz}: {self.localats}  {self.localoffset}'

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

    def get_local_time(self):
        return time.localtime(self.ts)

    def get_utc_time(self):
        return self.utcats


def different(self, other):
    """different(other)

    """

    result = False
    if isinstance(other, LocalWeather) and isinstance(self, LocalWeather):
        o = other
        mains = self.rjson['main']
        omains = other.rjson['main']
        return self.times['sunup'] != o.times['sunup'] or \
            self.times['sunset'] != o.times['sunset'] or \
            mains['temp'] != omains['temp'] or \
            mains['temp_min'] != omains['temp_min'] or \
            mains['temp_max'] != omains['temp_max'] or \
            self.rjson['wind'] != o.rjson['wind']

    return result


class LocalWeather(ComparableMixin):
    """ LocalWeather()


    """
    valid = False
    rjson = {}
    units = 'std'
    netstatus = []
    maint = {}

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
        self._load_from_json(other.rjson)

    def _load_from_json(self, js):
        """_load_from_json(js)

        Note that netstatus does not get copied over and is None

        """
        self.valid = True
        self.rjson = js
        sys = self.rjson['sys']

        self.times = {'dt': MyTime(self.rjson['dt']),
                      'sunup': MyTime(sys['sunrise']),
                      'sunset': MyTime(sys['sunset'])}
        mains = self.rjson['main']
        hum = float(mains['humidity'])
        wind = self.rjson['wind']
        speed = wind['speed']
        try:
            gust = wind['gust']
        except:
            gust = 0

        degree = round(float(wind['deg']), 0)
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
            self._load_from_json(self.rjson)

        except Exception as e:
            print(request_status)
            print(e)

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

    # def set_Units(self, u):  # std, metric, imperial
        # uu = u.lower()
        # if uu not in _VALID_UNITS:
        # raise ValueError("units must be std, metric, or imperial")
        # self.units = uu

    def get_DateTime(self, local=True):
        if local:
            return f'local: {self.times["dt"]["localats"]} {self.times["dt"]["localtz"]}'

        return f'utc: {self.times["dt"]["utcats"]}'

    def get_Weather(self):
        self.rjson['main']
        pass

    def get_wind(self, local=True):
        return self.maint['wind']

    def get_temp(self):
        """get_temp()

        Gets a tuple of current temp, min temp and max temp,
        each of which is a tuple of (kelven, centegrade, ferenhite ) all text
        """
        return self.maint['temp']


def main():
    # _lw = LocalWeather()
    # _lw.load()
    # print(f'valid: {_lw.valid}')
    # print(f'times:\t{_lw.times["dt"]}\n\tsunup:{_lw.times["sunup"]}\n\tsundown:{_lw.times["sunset"]}')
    # print(f'hum: {_lw.maint["humidity"]}, temp: {_lw.maint["temp"][0][2]}, wind: dir {_lw.maint["wind"]["dir"]}, speed: {_lw.maint["wind"]["speed"][1][1]}')
    # jp = jsonpickle.encode(_lw)
    # lwj = jsonpickle.encode(_lw)
    # duplw = jsonpickle.decode(lwj)
    # jjjj = _lw == dupl

    saved = []
    #restored = []
    #lwobjs = []
    _lw = LocalWeather()
    LocalWeather.__module__ = 'localweather'

    # for i in range(16):
    # _lw = LocalWeather()
    # _lw.load()
    # lwobjs.append(_lw)
    # lwj = jsonpickle.encode(_lw)
    # fl.write(lwj)
    # print('.', end='')
    # time.sleep(15)
    _lw.load()
    #aa = str(_lw)
    #bb = repr(_lw)
    #c = 0

    with open('testlocalWeather60.json', 'w') as fl:
        numreadings = 20
        delaymin = 7
        for i in range(numreadings):
            _lw = LocalWeather()
            _lw.load()
            saved.append(_lw)
            print('.', end='')
            if i >= numreadings - 1:
                continue
            for _ in range(4 * delaymin):
                time.sleep(15)
        try:
            # lw = LocalWeather()
            # LocalWeather.__module__ = 'localweather
            #jsons0 = jsonpickle.encode(saved[0])
            #val0 = jsonpickle.decode(jsons0)
            jsons = jsonpickle.encode(saved, unpicklable=True)
            # saved1 = jsonpickle.decode(jsons0, classes=(
            # LocalWeather, MyTime,))
            fl.write(jsons)
            # pickle.dump(saved, fl, fix_imports=False)
        except Exception as ex:
            a = 0

    """
    restored = []
    with open('testlocalWeather60.json', 'r') as fl1:

        try:
            jj = fl1.read()
            restored = jsonpickle.decode(jj, classes=(
                LocalWeather, MyTime,))
            a = 0
        except Exception as ex:
            a = 0
    a = 0
    """

    a = 0


if __name__ == '__main__':
    freeze_support()
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
        sys.exit()


