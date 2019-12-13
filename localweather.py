#!/usr/bin/env python3

"""tools for accessing the database"""
import os
import sys
import logging
import logging.handlers
import requests
# import json
# import mysql.connector as mariadb
import time
from medfordor import Medford_or_Info as MI


import dbtools


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/localweather'
OW_DEFAULTKEY = '&appid=a723524c61b7e34a683dfbc79bd683cd'
OW_RVMKEY = '&appid=1320944048cabbe1aebe1fbe9c1c7d6c'
OW_First = 'https://api.openweathermap.org/data/2.5/weather'

PAYLOAD = {'id': str(MI['id']), 'APPID': '1320944048cabbe1aebe1fbe9c1c7d6c'}

_DT = dbtools.DBTools()
_DB = _DT.dbase
_CU = _DT.cursor

_VALID_UNITS = ['std', 'metric', 'imperial']


class MyTime:
    """localweather.MYTime(timestamp=)
    if timestamp not specified uses the timestamp from the local time.

    """

    def __init__(self, timestamp=time.mktime(time.localtime())):
        self.ts = int(timestamp)
        self.locals = time.localtime(self.ts)
        self.local = time.asctime(self.locals)
        self.utc = time.asctime(time.gmtime(self.ts))
        self.localtz = self.locals.tm_zone
        self.localoffset = self.locals.tm_gmtoff / 3600  # 60*60

    def get(self):
        """get()

        returns a tupal of the timestamp, the utc and local times, the local time zone, and the local offset
        """
        return (self.ts, self.utc, self.local, self.localtz, self.localoffset,)

    def __str__(self):
        return f'utc: {self.utc},  {self.localtz}: {self.local}  {self.localoffset}'

    def __repr__(self):
        return f'localweather.MyTime, utc: {self.utc},  {self.localtz}: {self.local}  {self.localoffset}'

    def __eq__(self, other):
        return self.ts == other.ts

    def __ne__(self, other):
        return self.ts != other.ts

    def __hash__(self):
        return self.ts

    def __lt__(self, other):
        return self.ts < other.ts

    def __le__(self, other):
        return self.ts <= other.ts

    def __gt__(self, other):
        return self.ts > other.ts

    def __ge__(self, other):
        return self.ts >= other.ts


class LocalWeather:
    def load(self):

        r = requests.get(OW_First, params=PAYLOAD)
        self.netstatus = r.status_code
        if not r.status_code == 200:
            raise Exception(f'{r.url} returned {r.status_code}')

        try:
            self.rjson = r.json()
            self.valid = True
            sys = self.rjson['sys']
            #aa = MyTime(self.rjson['dt'])
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
            rspeed = self.convertspeed(speed)
            rgust = self.convertspeed(gust)

            self.maint = {'temp': (self.converttemp(mains['temp']), self.converttemp(mains['temp_min']), self.converttemp(mains['temp_max'])),
                          'humidity': f'{hum:.1f}%',
                          'wind': {'speed': ((f'{rspeed[0]:.1f} m/s', f'{rspeed[1]:.1f} mph'), (f'{rgust[0]:.1f} m/s', f'{rgust[1]:.1f} mph')), 'dir': f'{degree:.0f} degrees'},
                          'times': {'acquire': self.times['dt'].get()[2], 'sunup': self.times['sunup'].get()[2], 'sunset': self.times['sunset'].get()[2]}
                          }
            a = 0

        except Exception as e:
            print(r)
            print(e)
            a = 0

    def __init__(self):
        """LocalWeather()


        """
        self.valid = False
        self.rjson = {}
        self.units = 'std'
        self.netstatus = ''
        # self.load()
        #r = requests.get(OW_First, params=PAYLOAD)
        #self.netstatus = r.status_code
        # if not r.status_code == 200:
        # raise Exception(f'{r.url} returned {r.status_code}')

        # try:
        #self.rjson = r.json()
        #self.valid = True
        #sys = self.rjson['sys']
        ##aa = MyTime(self.rjson['dt'])
        # self.times = {'dt': MyTime(self.rjson['dt']),
        # 'sunup': MyTime(sys['sunrise']),
        # 'sunset': MyTime(sys['sunset'])}
        #mains = self.rjson['main']
        #hum = float(mains['humidity'])
        #wind = self.rjson['wind']
        #speed = wind['speed']
        # try:
        #gust = wind['gust']
        # except:
        #gust = 0

        #degree = round(float(wind['deg']), 0)
        #rspeed = self.convertspeed(speed)
        #rgust = self.convertspeed(gust)

        # self.maint = {'temp': (self.converttemp(mains['temp']), self.converttemp(mains['temp_min']), self.converttemp(mains['temp_max'])),
        # 'humidity': f'{hum:.1f}%',
        # 'wind': {'speed': ((f'{rspeed[0]:.1f} m/s', f'{rspeed[1]:.1f} mph'), (f'{rgust[0]:.1f} m/s', f'{rgust[1]:.1f} mph')), 'dir': f'{degree:.0f} degrees'},
        # 'times': {'acquire': self.times['dt'].get()[2], 'sunup': self.times['sunup'].get()[2], 'sunset': self.times['sunset'].get()[2]}
        # }
        #a = 0

        # except Exception as e:
        # print(r)
        # print(e)
        #a = 0

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
        # result = f'{self.times['dt']
        pass

    def get_Weather(self):
        self.rjson['main']
        pass

    def get_wind(self, local=True):
        return self.maint['wind']

    def get_temp(self):
        return self.maint['temp']

    def converttemp(self, k):
        """converttemp(k)
        k is degrees in Kelven

        returns 3truple (xK, xC, xF)
        """
        #c = 0.0
        k1 = 0.0
        try:
            k1 = float(k)
        except ValueError as e:
            raise ValueError(
                'f(t) is not int, float or text of a float or int number')

        c = k1 - 273.15
        f = (c * (9 / 5)) + 32.0
        temptup = (f'{k:.2f}K', f'{c:.2f}C', f'{f:.2f}F',)
        return temptup

    def convertspeed(self, msin):
        """convertspeed(msin)
        msin - meters per seconds

        return tuple (meters per sec, miles per hour)
        """
        ms = float(msin)
        mh = ms * 2.236936
        return (ms, round(mh, 2))


def main():

    lt = MyTime()
    lts = str(lt)
    lt1 = MyTime(timestamp=1575520318)
    lt1s = str(lt1)

    lw = LocalWeather()
    lw.converttemp('10.5')
    c = 0

    a = 0
    # time is unix UTC


if __name__ == '__main__':
    if not os.path.isdir(LOG_DIR):
        os.mkdir(LOG_DIR)

    LF_HANDLER = logging.handlers.RotatingFileHandler(
        ''.join([LOG_DIR, LOG_FILE, ]),
        maxBytes=10000,
        backupCount=5,
    )
    LF_HANDLER.setLevel(logging.DEBUG)
    LC_HANDLER = logging.StreamHandler()
    LC_HANDLER.setLevel(logging.DEBUG)  # (logging.ERROR)
    LF_FORMATTER = logging.Formatter(
        '%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
    LC_FORMATTER = logging.Formatter(
        '%(name)s: %(levelname)s - %(message)s')
    LC_HANDLER.setFormatter(LC_FORMATTER)
    LF_HANDLER.setFormatter(LF_FORMATTER)
    THE_LOGGER = logging.getLogger()
    THE_LOGGER.setLevel(logging.DEBUG)
    THE_LOGGER.addHandler(LF_HANDLER)
    THE_LOGGER.addHandler(LC_HANDLER)
    THE_LOGGER.info('localweather executed as main')
    # LOGGER.setLevel(logging.DEBUG)

    # UI = UserInput()

    try:
        main()
        pass

    except(Exception, KeyboardInterrupt) as exc:
        sys.exit(str(exc))

    finally:
        sys.exit()
# {
# "id": 5740099,
# "name": "Medford",
# "country": "US",
# "coord": {
# "lon": -122.875587,
# "lat": 42.326519
# }
