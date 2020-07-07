#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os
import logging
import logging.handlers
import datetime
from collections import namedtuple
# from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque
from typing import Any, Tuple, List, Dict, Set, Callable


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/smeter'

SMArgkeys = namedtuple('SMArgkeys', [
    'c',
    'f'])

_SREAD: Tuple[Tuple[float, float, Any]] = (
    (-127.0, -121.0, 0),
    (-121.0, -115.0, 1, ),
    (-115.0, -109.0, 2, ),
    (-109.0, -103.0, 3, ),
    (-103.0, -97.0, 4, ),
    (-97.0, -91.0, 5, ),
    (-91.0, -85.0, 6, ),
    (-85.0, -79.0, 7, ),
    (-79.0, -73.0, 8, ),
    (-73.0, -63.0, 9, ),
    (-63.0, -53.0, '9+10'),
    (-53.0, -43.0, '9+20'),
    (-43.0, -33.0, '9+30'),
    (-33.0, -23.0, '9+40'),
    (-23.0, -13.0, '9+50'),
    (-13.0, -3.0, '9+60'),
    (-3.0, 0.0, '9+70'),
    (0.0, 0.0, '9+70+'),
)


class SMeter:
    """SMeter(argin)

    argin is a 2 argument named tuple (argin:SMArgkeys)
    freq is an integer
    arg is the result from a ZZSM; cat command and looks like "ZZSM ABC;" where
    ABC are three digits from 000 to 260

    P1 = 000 to 260
    ZZSM reads the received signal strength in dBm where S9 = -73 dBm. The range is -140 dBm to
    -10 dBm with a scale factor of 2 (P2 max = 260). The actual signal strength, in dBm,
    is the value of ZZSM divided by 2 minus 140.
    """

    # def __init__(self, argin: Tuple[str, int]):
    def __init__(self, argin: SMArgkeys):
        if isinstance(argin, list):
            raise ValueError

        arg: str = argin.c
        freq: int = argin.f
        try:
            _var = int(arg[4:-1])  # get the ABC
        except Exception as _jj:
            print(_jj)
            _var = 0
        _dBm = (_var / 2.0) - 140.0
        self.signal_st: Dict[str, Any] = {'sl': 's?'}
        self.signal_st['dBm'] = _dBm
        self.time: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.freq: int = freq

        if self.signal_st.get('dBm') <= -127.0:
            self.signal_st['sl'] = 'S0'
        else:
            for _ in _SREAD:
                if self.signal_st.get('dBm') >= _[0] \
                   and self.signal_st.get('dBm') < _[1]:
                    self.signal_st['sl'] = f'S{_[2]}'
                    break

    def __str__(self):
        return f'[SMeter: freq:{self.freq}, {self.signal_st.get("dBm") :.5f}dBm, { self.signal_st.get("sl")}]' \


    def __repr__(self):
        return f'SMeter: freq:{self.freq}, {self.signal_st.get("dBm") :.5f}dBm, {self.signal_st.get("sl")}' \


    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.signal_st.get('dBm') < other.signal_st.get('dBm')
        return False

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.signal_st.get('dBm') <= other.signal_st.get('dBm')
        return False

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    # def __ne__(self, other):
        # return not self.__eq__(other)

    def __gt__(self, other):

        if isinstance(other, self.__class__):
            return self.signal_st.get('dBm') > other.signal_st.get('dBm')
        return False

    def __ge__(self, other):

        if isinstance(other, self.__class__):
            return self.signal_st.get('dBm') >= other.signal_st.get('dBm')
        return False

    def __hash__(self):
        return id(self)


def main():
    """main()

    """
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
    THE_LOGGER.info('smeter executed as main')
    # LOGGER.setLevel(logging.DEBUG)
    try:
        main()

    except(Exception, KeyboardInterrupt) as exc:
        sys.exit(str(exc))

    finally:
        sys.exit('smeter normal exit')
