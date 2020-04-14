#!/usr/bin/env python3

"""tools for accessing the database"""
import os
import sys
import logging
import logging.handlers
from typing import List, Sequence, Dict, Mapping, Any, Tuple
import jsonpickle
import mysql.connector as mariadb
import datetime
from datetime import tzinfo, timezone
from datetime import datetime as Dtc
from datetime import timedelta as Tdelta

import smeteravg
from noisefloor import NFResult
from bandreadings import Bandreadings
from timestampaux import get_bigint_timestamp, get_float_timestamp


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/dbtools'


class DBTools:
    """DBTools

    """
    try:
        from noisefloor import NFResult
    except ImportError as ie:
        import sys
        noisefloor = sys.modules[__package__ + '.NFresult']

    def __init__(self, dbid: str = "python1"):
        self.dbid = dbid
        self.dbase = mariadb.connect(
            host="localhost",
            user="dbcurtis",
            passwd="YAqGJ7brzOBDnUJnwXQT",
            database=self.dbid,
            autocommit=False
        )
        self.cursor = self.dbase.cursor()
        self.opened = False
        self.connected = True
        utc1 = Dtc.now(timezone.utc)
        local = utc1.astimezone()
        self._localtz = local.tzinfo

    def __str__(self):
        return f'Schema is {self.dbid}, opened = {self.opened}, connected = {self.connected}'

    def __repr__(self):
        return f'DBTools: Schema is {self.dbid}, opened = {self.opened}, connected = {self.connected}'

    def open(self) -> bool:
        """open()

        """
        if self.opened:
            raise Exception('database already opened')
        self.opened = self.connected and True
        return self.opened

    def close_and_disconnect(self):
        """close()

        ok to do multiple closes once closed,
        need to have a new object to re open --- is this true?

        """
        if self.opened:
            self.dbase.commit()
            self.dbase.disconnect()
            self.opened = False
            self.connected = False

        elif self.connected:
            self.dbase.disconnect()
            self.connected = False

    def save_band_noisefloor(self, nfin: NFResult):
        def mksql(nf: NFResult) -> List[str]:
            result: List[Bandreadings] = []
            return result

        if not nfin.completed():
            raise ValueError('NFResult not complete')

        sqllst: List[str] = []

        sqllst.append(mksql(nfin))

        pass

    # def save_localweather(self, lw: LocalWeather):
        # pass

    def set_timeref(self, cmt: str = None) -> Tuple[int, float, Dtc, str]:
        """set_timeref(cmt=None)
        cmt can be a string comment stored in the db

          returns a tuple of(db index, timestamp, Local datetime, comment text)
        """
        if not self.opened:
            raise Exception('database not opened')

        ts2: int = get_bigint_timestamp()
        sql = f"INSERT INTO times SET datetime ={ts2}, comment = '{cmt}' ;"
        self.cursor.execute(sql)
        self.dbase.commit()
        return self.get_timeref()

    def get_timeref(self) -> Tuple[int, float, Dtc, str]:
        """getrecid()

        returns a tuple of(db index, timestamp, Local datetime, comment text)

        to get a text of the local date time, use get_timeref()[2].strftime('%Y/%m/%d %H:%M:%S')
        for format see: https://docs.python.org/3.8/library/datetime.html#strftime-strptime-behavior



        """
        if not self.opened:
            raise Exception('database not opened')
        self.cursor.execute(
            'SELECT * FROM times ORDER BY TIMERECID DESC LIMIT 1;')
        records = self.cursor.fetchall()
        idx: int = records[0][0]
        # val: int = records[0][1]
        cmt: str = records[0][2]
        # val1: float = val / 1000000.0
        val1: float = get_float_timestamp(records[0][1])
        utc = Dtc.fromtimestamp(val1, timezone.utc)
        local = utc.astimezone(self._localtz)
        #txt = local.strftime('%Y/%m/%d %H:%M:%S')

        result = (idx, val1, local, cmt)
        return result

    def resetdb(self):
        try:
            self.open()
        except Exception:
            pass

        truncatelst = [f"TRUNCATE TABLE weather;", f"TRUNCATE TABLE bandreadings;", f"TRUNCATE TABLE times;"]
        for sql in truncatelst:
            self.cursor.execute(sql)
        self.dbase.commit()

    def get_lw_recid(self) -> List[int]:
        if not self.opened:
            raise Exception('database not opened')
        try:

            self.cursor.execute(
                'SELECT WRECID, TIMERECID FROM weather ORDER BY WIDEX DESC LIMIT 1;')
            records = self.cursor.fetchall()
            if not records:
                return None
            return records[0]
        except Exception as jj:
            a = 0
            return None

    def get_br_recid(self) -> List[int]:
        if not self.opened:
            raise Exception('database not opened')
        try:
            self.cursor.execute(
                'SELECT BRRECID, TIMERECID, lwrecid FROM bandreadings ORDER BY BRRECID DESC LIMIT 1;')
            records = self.cursor.fetchall()
            if not records:
                return None
            return records[0]
        except Exception as jj:
            a = 0
            return None


def main():
    from localweather import LocalWeather

    try:
        dbt = DBTools(dbid='python1test')
        dbt.open()
        lwidx = dbt.get_lw_recid()
        if not None is lwidx:
            print ('wrong result')

        local_weather_lst = []
        _lw = LocalWeather()
        with open('./tests/testlocalWeather60.json', 'r') as fl1:
            try:
                kk = fl1.read()
                local_weather_lst = jsonpickle.decode(
                    kk, classes=(LocalWeather, MyTime,))
                a = 0
            except Exception as ex:
                a = 0
        #deck = deque(local_weather_lst)
        lw1: LocalWeather = local_weather_lst[0]
        a = 0
    except:
        print('unexpected exception')
        a = 0
    finally:
        dbt.close_and_disconnect()

    a = 0


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
    LC_FORMATTER = logging.Formatter('%(name)s: %(levelname)s - %(message)s')
    LC_HANDLER.setFormatter(LC_FORMATTER)
    LF_HANDLER.setFormatter(LF_FORMATTER)
    THE_LOGGER = logging.getLogger()
    THE_LOGGER.setLevel(logging.DEBUG)
    THE_LOGGER.addHandler(LF_HANDLER)
    THE_LOGGER.addHandler(LC_HANDLER)
    THE_LOGGER.info('dbtools executed as main')
    # LOGGER.setLevel(logging.DEBUG)

    try:
        main()

    except(Exception, KeyboardInterrupt) as exc:
        sys.exit(str(exc))

    finally:
        sys.exit('normal exit')
