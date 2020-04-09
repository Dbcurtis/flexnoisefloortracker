#!/usr/bin/env python3

"""tools for accessing the database"""
import os
import logging
import logging.handlers
from typing import List, Sequence, Dict, Mapping, Any
#import mysql.connector as mariadb
#import datetime

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/medfordor'

# the following is useful for finding out what these values mean
# https://www.geonames.org

Medford_or_Info: Dict[str, Any] = {
    "id": 5740099,
    "coord": {
        "lon": -122.875587,
        "lat": 42.326519
    },
    "country": "US",
    "geoname": {
        "cl": "P",
        "code": "PPLA2",
        "parent": 5733351
    },
    "langs": [
        {
            "de": "Medford"
        },
        {
            "en": "Medford"
        },
        {
            "io": "Medford"
        },
        {
            "link": "http://en.wikipedia.org/wiki/Medford%2C_Oregon"
        },
        {
            "post": "97504"
        },
        {
            "pt": "Medford"
        },
    ],
    "name": "Medford",
    "stat": {
        "level": 1.0,
        "population": 74907
    },
    "stations": [
        {
            "id": 2298,
            "dist": 4,
            "kf": 1
        },
        {
            "id": 2317,
            "dist": 28,
            "kf": 1
        },
        {
            "id": 10832,
            "dist": 37,
            "kf": 1
        },
        {
            "id": 29765,
            "dist": 37,
            "kf": 1
        },
        {
            "id": 30701,
            "dist": 13,
            "kf": 1
        },
        {
            "id": 31217,
            "dist": 15,
            "kf": 1
        },
        {
            "id": 32028,
            "dist": 18,
            "kf": 1
        },
        {
            "id": 32424,
            "dist": 38,
            "kf": 1
        },
        {
            "id": 32594,
            "dist": 2,
            "kf": 1
        },
        {
            "id": 32708,
            "dist": 2,
            "kf": 1
        },
        {
            "id": 32752,
            "dist": 16,
            "kf": 1
        },
        {
            "id": 34024,
            "dist": 5,
            "kf": 1
        },
        {
            "id": 34076,
            "dist": 22,
            "kf": 1
        },
        {
            "id": 34733,
            "dist": 3,
            "kf": 1
        },
        {
            "id": 34736,
            "dist": 43,
            "kf": 1
        }
    ],
    "zoom": 6
}


def LOCATION(_): return (Medford_or_Info.get('coord'),)


def main():
    pass


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
    THE_LOGGER.info('medfordor executed as main')
    # LOGGER.setLevel(logging.DEBUG)

    try:
        main()
        pass

    except(Exception, KeyboardInterrupt) as exc:

        sys.exit(str(exc))

    finally:
        sys.exit()
