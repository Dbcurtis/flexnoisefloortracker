#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os
import logging
import logging.handlers
from typing import List, Tuple
#from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict

from datetime import datetime as Dtc
from datetime import timezone
import math
from smeter import _SREAD, SMeter, SMArgkeys
import timestampaux


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/smeteravg'

NOISE_TYPES = ('lownoise', 'highnoise', 'midnoise', )


class SMeterAvg:
    """SMeterAvg(argin,band)

    argin is a list of SMeter,
    band is a band indicator

    """

    def __init__(self, argin: List[SMeter], band):
        def _init_phase1(arg):
            self.freqs = {_.freq for _ in arg}
            # tot = sum([_sm.signal_st.get('dBm') for _sm in arg])
            # self.dBm = {}
            self.dBm['adBm'] = sum([_sm.signal_st.get('dBm')
                                    for _sm in arg]) / len(arg)
            self.dBm['mdBm'] = get_median(arg[:])
            self.dtime: Dtc = Dtc.now(timezone.utc)
            local: Dtc = self.dtime.astimezone()
            self.time: str = local.strftime('%Y-%m-%d %H:%M:%S')

            self.smlist = arg[:]

            def scoperv0():
                var = 0
                for _sm in arg:
                    var += (_sm.signal_st.get('dBm')
                            - self.dBm.get('adBm')) ** 2

                var /= (len(arg) - 1)
                self.signal_st['var'] = var
                self.signal_st['stddv'] = var ** .5
                self.signal_st['sl'] = 's?'
                self.v = 0
            # scoperv0()

            def scoperv1():
                stddev = self.signal_st.get('stddv')
                median = self.dBm.get('mdBm')
                toplownoise = median - stddev - 0.000000000001
                bottomhighnoise = median + stddev + 0.000000000001
                lownoise = []
                highnoise = []
                midnoise = []
                for _sm in arg:
                    sig = _sm.signal_st.get('dBm')
                    if sig < toplownoise:
                        lownoise.append(_sm)
                    elif toplownoise < sig < bottomhighnoise:
                        midnoise.append(_sm)
                    else:
                        highnoise.append(_sm)

                self.noise['lownoise'] = lownoise
                self.noise['highnoise'] = highnoise
                self.noise['midnoise'] = midnoise
                self.v = 1

            def scoperv2():

                # self.singlenoisefreq = len(self.get_noise_freqs()) == 1
                self.v = 2

            def scoperv3():
                self.v = 3
                self.noise = {}

            scoperv0()
            scoperv1()
            scoperv2()
            scoperv3()

        arg = argin
        self.freqs = {}
        self.dBm = {}
        self.time = None
        self.band = band
        self.smlist = []
        self.noise = {}
        self.signal_st = {'var': None, 'stddv': None, 'sl': None, }
        self.usable = True
        try:
            _init_phase1(arg)
        except ZeroDivisionError as sde:
            self.signal_st['var'] = 1000
            self.signal_st['stddv'] = 1000
            self.signal_st['sl'] = 'sE'
            self.v = 0
            return

        if self.dBm.get('adBm') <= -127.0:
            self.signal_st['sl'] = 'S0'
        else:
            for _ in _SREAD:
                mdbm = self.dBm.get('mdBm')
                if _[0] <= mdbm < _[1]:
                    self.signal_st['sl'] = 'S{}'.format(_[2])
                    break

    def gen_sql(self) -> str:

        # sss = dbtools.get_bigint_timestamp(self.times['dt'])
        # trecdt: int = dbtools.get_bigint_timestamp(self.times['dt'])
        # tsup: int = dbtools.get_bigint_timestamp(self.times['sunup'])
        # tsdn: int = dbtools.get_bigint_timestamp(self.times['sunset'])
        sl: str = self.signal_st['sl']
        stdev: float = self.signal_st['stddv']
        timedone: int = timestampaux.get_bigint_timestamp(self.dtime)
        jjj: List[str] = [
            f"timedone = {timedone},",
            f"band = {self.band},",
            f"adBm = {self.dBm['adBm']},",
            f"mdBm = {self.dBm['adBm']},",
            f"sval = '{sl}',",
            f"stdev = {stdev}"
        ]
        sets: str = ' '.join(jjj)
        result: str = f'INSERT INTO bandreadings SET {sets}'
        return result

    def get_start_time_of_readings(self) -> List[Tuple[str, int]]:
        """get_start_time_of_readings()

        returns a list of tupales with (str datetime, int freq)
        for all readings that make up the average
        """
        result: List[Tuple[str, int]] = []
        for sm in self.smlist:
            result.append((sm.time, sm.freq,))

        return result

    def __str__(self):
        result = ''
        try:
            s = self
            result = f"[b:{s.band}, {s.dBm.get('adBm'):.5f}adBm, {s.dBm.get('mdBm'):.5f}mdBm, {s.signal_st.get('sl')}, \
var: {s.signal_st.get('var'):.5f}, stddv: {s.signal_st.get('stddv'):.5f}]"  # \

        except Exception:
            result = 'old version of SMeterAvg'

        return result

    def __repr__(self):
        result = ''
        try:
            s = self
            result = f"[SMeterAvg: b:{s.band}, {s.dBm.get('adBm'):.5f}adBm, {s.dBm.get('mdBm'):.5f}mdBm, {s.signal_st.get('sl')}, \
var: {s.signal_st.get('var'):.5f}, stddv: {s.signal_st.get('stddv'):.5f}]"

        except Exception:
            result = 'old version of SMeterAvg'

        return result


# -----------------------------------


def get_median(lst: List[SMeter]) -> float:
    """get_median(lst)

    lst is a list/of SMeter
    """
    if lst is None:
        raise ValueError('None not allowed')
    if not isinstance(lst, list):
        raise ValueError('lst needs to be a list')
    if not lst:
        raise ValueError('list needs at least one element')

    lst.sort()
    lstsize: int = len(lst)
    iseven: bool = (lstsize % 2) == 0
    median: float = None
    if isinstance(lst[0], SMeter):

        if iseven:
            mididx = int(lstsize / 2)
            median = (lst[mididx - 1].signal_st.get('dBm')
                      + lst[mididx].signal_st.get('dBm')) / 2
        else:
            mididx = lstsize - \
                1 if lstsize == 1 else int(math.trunc((lstsize) / 2))
            median = lst[mididx].signal_st.get('dBm')
    else:

        if iseven:
            mididx = int(lstsize / 2)
            median = (lst[mididx - 1] + lst[mididx]) / 2
        else:
            mididx = lstsize - \
                1 if lstsize == 1 else int(math.trunc((lstsize) / 2))
            median = lst[mididx]
    return median


def factory(arg, *args, **kwargs):
    """factory(arg,*args,**kwargs)


    """
    def versionadj(version, sma):
        _debugversion = version

        return SMeterAvg(sma.smlist, sma.band)

    if isinstance(arg, list):
        return SMeterAvg(arg, args[0])

    if isinstance(arg, SMeterAvg):
        sma = arg
        _v = None

        try:
            _v = sma.v

        except Exception:
            _v = 0

        return versionadj(_v, sma)
    return None


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
    THE_LOGGER.info('smeteravr executed as main')
    # LOGGER.setLevel(logging.DEBUG)
    try:
        main()

    except(SystemExit, KeyboardInterrupt) as exc:
        sys.exit(str(exc))

    finally:
        sys.exit('smeteravg normal exit')
