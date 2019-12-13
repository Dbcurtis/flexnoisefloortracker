#!/usr/bin/env python3

"""tools for accessing the database"""
import os
import logging
import logging.handlers
import mysql.connector as mariadb
import datetime
from suntime import Sun, SunTimeException
import dbtools
from medfordor import LOCATION


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/daylight'

_DT = dbtools.DBTools()
_DB = _DT.dbase
_CU = _DT.cursor


class Daylight:

    def __init__(self):
        lldic = medfordor.LOCATION(_)[0]
        self.sun = Sun(lldic.get('lat'), lldic.get('lon'))
        self.times = {}
        self.times['lsr'] = self.sun.get_Local_Sunrise_time()
        self.times['lss'] = self.sun.get_Local_Sunset_time()
        self.times['utcsr'] = sun.get_sunrise_time()
        self.times['utcss'] = sun.get_sunset_time()

    def __str__(self):
        return f'{self.srt.date()}: SR: {self.srt.time()}, SS: {self.sst.time()}'

    def __repr__(self):
        return f'[Daylight: {self.srt.date()}: SR: {self.srt.time()}, SS: {self.sst.time()}]'


def main():
    dl = Daylight()
    str = str(dl)
    rep = repr(dl)


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
    THE_LOGGER.info('daylight executed as main')
    # LOGGER.setLevel(logging.DEBUG)

    try:
        main()
        pass

    except(Exception, KeyboardInterrupt) as exc:

        sys.exit(str(exc))

    finally:

        sys.exit()
