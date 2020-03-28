#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os
import logging
import logging.handlers
import datetime
import math

from smeter import _SREAD, SMeter
from typing import List, Tuple


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/smeteravg'

NOISE_TYPES = ('lownoise', 'highnoise', 'midnoise', )


# def get_median(lst):
# """get_median(lst)

# lst is a list/of SMeter
# """
# if lst is None:
#raise ValueError('None not allowed')
# if not isinstance(lst, list):
#raise ValueError('lst needs to be a list')
# if not lst:
#raise ValueError('list needs at least one element')

# lst.sort()
#lstsize = len(lst)
#iseven = (lstsize % 2) == 0
#median = None
# if isinstance(lst[0], SMeter):

# if iseven:
#mididx = int(lstsize / 2)
# median = (lst[mididx - 1].signal_st.get('dBm') +
# lst[mididx].signal_st.get('dBm')) / 2
# else:
# mididx = lstsize - \
#1 if lstsize == 1 else int(math.trunc((lstsize) / 2))
#median = lst[mididx].signal_st.get('dBm')
# else:

# if iseven:
#mididx = int(lstsize / 2)
#median = (lst[mididx - 1] + lst[mididx]) / 2
# else:
# mididx = lstsize - \
#1 if lstsize == 1 else int(math.trunc((lstsize) / 2))
#median = lst[mididx]
# return median


# def factory(arg, *args, **kwargs):
# """factory(arg,*args,**kwargs)

# """
# def versionadj(version, sma):
#_debugversion = version

# return SMeterAvg(sma.smlist, sma.band)

# if isinstance(arg, list):
# return SMeterAvg(arg, args[0])

# if isinstance(arg, SMeterAvg):
#sma = arg
#_v = None

# try:
#_v = sma.v

# except Exception:
#_v = 0

# return versionadj(_v, sma)
# return None


class SMeterAvg:
    """SMeterAvg(argin,band)

    argin is a list of SMeter,
    band is a band indicator

    """

    def __init__(self, argin, band):
        def _init_phase1(arg):
            self.freqs = {_.freq for _ in arg}
            # tot = sum([_sm.signal_st.get('dBm') for _sm in arg])
            # self.dBm = {}
            self.dBm['adBm'] = sum([_sm.signal_st.get('dBm')
                                    for _sm in arg]) / len(arg)
            self.dBm['mdBm'] = get_median(arg[:])
            self.time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.smlist = arg[:]

            def scoperv0():
                var = 0
                for _sm in arg:
                    var += (_sm.signal_st.get('dBm') -
                            self.dBm.get('adBm')) ** 2

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

                self.singlenoisefreq = len(self.get_noise_freqs()) == 1
                self.v = 2

            scoperv0()
            scoperv1()
            scoperv2()

        arg = argin
        self.freqs = {}
        self.dBm = {}
        self.time = None
        self.band = band
        self.smlist = []
        self.noise = {}
        self.signal_st = {'var': None, 'stddv': None, 'sl': None, }
        self.usable = True

        _init_phase1(arg)

        if self.dBm.get('adBm') <= -127.0:
            self.signal_st['sl'] = 'S0'
        else:
            for _ in _SREAD:
                mdbm = self.dBm.get('mdBm')
                if _[0] <= mdbm < _[1]:
                    self.signal_st['sl'] = 'S{}'.format(_[2])
                    break

    def get_noise_freqs(self, type='highnoise'):
        """get_noise_freqs(type=val)

        val = 'highnoise', 'midnoise', or 'lownoise'

        """
        if type not in NOISE_TYPES:
            raise ValueError(
                'illegal noise type: highnoise, midnoise, lownoise')
        return {sm.freq for sm in self.noise.get(type)}

    def badness(self):
        """badness()

        returns rzdio of high noise readings to low and mid noise readings
        calculated by nf = number of frequences checked,
        rf is readings per freq
        nhr is number of high readings
        nrt is total readings
        bad is nhr/(nrt-nhr)

        """
        result = None
        if self.noise:
            nlr = len(self.noise.get('lownoise'))
            nmr = len(self.noise.get('midnoise'))
            nhr = len(self.noise.get('highnoise'))
            # nrt = nlr + nmr + nhr

            result = nhr / (nlr + nmr)

        return result

    def get_start_time_of_readings(self) -> List[Tuple]:
        """get_start_time_of_readings()

        returns a list of tupales with (str datetime, int freq)
        for all readings that make up the average
        """
        result = []
        for sm in self.smlist:
            result.append((sm.time, sm.freq,))

        return result

    def get_quiet(self):  # -> SMeterAvg:
        """get_quiet()

        returns new SMeterAvg using only the midnoise and lownoise readings if badness is less than
        0.2
        """
        result = None
        #_debugb = self.badness()
        if self.badness() < 0.334:
            result = SMeterAvg(self.noise.get('midnoise') +
                               self.noise.get('lownoise'), self.band)
        return result

    def get_noise(self):  # -> SMeterAvg:
        """get_noise()

        returns new SMeterAvg using only the midnoise and high noise readings
        """

        result = SMeterAvg(self.noise.get('midnoise') +
                           self.noise.get('highnoise'), self.band)
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

    # def get_out_of_var(self):
        # """get_out_of_var()

        # returns the SMeter (max_SM) with the max out of variance
        # and the other SMeters
        # """
        ## other = self.smlist[:]
        #max_SM = self.deva.get('max')[1]
        #other = [aa for aa in self.smlist if aa.freq != max_SM.freq]
        # return (max_SM, other)

# -----------------------------------


def get_median(lst) -> float:
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
    lstsize = len(lst)
    iseven = (lstsize % 2) == 0
    median = None
    if isinstance(lst[0], SMeter):

        if iseven:
            mididx = int(lstsize / 2)
            median = (lst[mididx - 1].signal_st.get('dBm') +
                      lst[mididx].signal_st.get('dBm')) / 2
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


def get_quiet(sma: SMeterAvg) -> SMeterAvg:
    """get_quiet()

    returns new SMeterAvg using only the midnoise and lownoise readings if badness is less than
    0.2
    """
    result = sma
    #_debugb = self.badness()
    if sma.badness() < 0.334:
        result = SMeterAvg(sma.noise.get('midnoise') +
                           sma.noise.get('lownoise'), sma.band)
    return result


def get_noise(sma: SMeterAvg) -> SMeterAvg:
    """get_noise()

    returns new SMeterAvg using only the midnoise and high noise readings
    """
    result = sma
    if len(sma.noise.get('highnoise')):
        result = SMeterAvg(sma.noise.get('midnoise') +
                           sma.noise.get('highnoise'), sma.band)
    return result


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
