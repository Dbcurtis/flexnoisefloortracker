#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import os
import logging
import logging.handlers
#import typing
from typing import List, Sequence, Mapping, Tuple, Dict, Any
from smeter import SMeter


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/postproc'

_MODE = {
    '00': 'LSB',
    '01': 'USB',
    '03': 'CWL',
    '04': 'CWU',
    '05': 'FM',
    '06': 'AM',
    '07': 'DIGU',
    '09': 'DIGL',
    '10': 'SAM',
    '11': 'NFM',
    '12': 'DFM',
    '20': 'FDV',
    '30': 'RTTY',
    '40': 'DSTR',
}


def zzmdpost(code):
    """zzmdpost(code):

    """
    if not code in _MODE.keys():
        return '??'
    return _MODE.get(code)


def zzifpost(resulttup):
    """zzifpost(resulttup)

    resulttup[0] is the result from the zzif command
    resulttup[1] is:

    P1 (11 characters) VFO A frequency in Hz. Same as ZZFA;
    P2 (4 characters) Frequency step size (0001 = 10 Hz/1000 = 50 Hz)
    P3 (6 characters) RIT/XIT frequency (+nnnnn or -nnnnn). *
    P4 (1 character) RIT status. 0 = off, 1 = on. *
    P5 (1 character) XIT status. 0 = off, 1 = on. *
    P6 (1 character) Channel bank number. Not used, defaulted to 0.
    P7 (2 characters) Channel bank number. Not used, defaulted to 00.
    P8 (1 character) MOX button status. 0 = off, 1 = on (transmitting).
    P9 (2 character) Operating mode. See ZZMD for settings.
    P10 (1 character) VFO Split status. Same as FR.
    P11 (1 character) Scan status. Not used, defaulted to 0.
    P12 (1 character) VFO Split status. Same as FT.
    P13 (1 character) CTCSS tone. Not used, defaulted to 0.
    P14 (2 characters) More tone controls. Not used, defaulted to 00.
    P15 (1 character) Shift status. Not used, defaulted to 0.
    """
    result = resulttup[0]
    if len(result) != 41:
        raise Exception('bad result')

    ret = {}
    ret['cmd'] = result[0:4]

    temp = result[4:]
    ret['freq'] = temp[0:11]
    temp = temp[11:]
    ret['stepsize'] = temp[0:4]
    temp = temp[4:]
    ret['ritF'] = temp[0:6]
    temp = temp[6:]
    ret['rits'] = temp[0:1]
    ret['xits'] = temp[1:2]
    temp = temp[2:]
    _p67 = temp[0:3]
    temp = temp[3:]
    ret['mox'] = temp[0:1]
    temp = temp[1:]
    ret['mode'] = zzmdpost(temp[0:2])
    temp = temp[2:]
    return ret

# def savemode(arg):
    # """savemode()

    # """
    #junk = arg
    # pass


# def save_freq(arg):
    # """saveFreq()

    # """
    #_ = arg
    # pass

# def save_dsp_filter(arg):
    # """saveDSPFilter()

    # """
    #_ = arg
    # pass

# def save_agc_mode(arg):
    # """saveAGCMode()

    # """
    #_ = arg
    # pass

# def savewnb(arg):
    # """savewnb()

    # """
    #_ = arg
    # pass

# def savenb(arg):
    # """savenb()

    # """
    #_ = arg
    # pass


def smeter(arg):  # (arg, freq):
    """smeter()
    """
    return SMeter(arg)


""" INITIALZE_FLEX
commands to set the radio to an initial condition. To be used after
    the current radio state is saved by savstate = flex.save_current_state()
    and the flex restored via flex.restore_state(savestate)

    # initalize the radio to a defined set of initial conditions.
"""
INITIALZE_FLEX = [

    # initalize the radio to a defined set of initial conditions.
    'ZZTX0;',  # set MOX off
    'ZZAR000;',  # set vfo A agc threshhold to 0
    'ZZAS000;',  # set vfo B agc threshhold to 0
    'ZZBI0;',  # Sets Binaural RX State off
    'ZZMD07;',  # Sets VFO A DSP Mode to 7 (DIGU)
    'ZZME07;',  # Sets VFO B DSP Mode to 7 (DIGU)
    'ZZFA00014150000;',  # sets VFO A to  14,150,000
    'ZZFB00007150000;',  # sets VFO B to  07,150,000
    'ZZFI04;',  # sets VFO A DSP filter to 04 (1K on DIGU I think)
    'ZZFJ04;',  # sets VFO B DSP filter to 04 (1K on DIGU I think)
    'ZZGT0;',  # sets VFO A AGC Mode to 0 (off)
    'ZZLB050;',  # Sets VFO A Audio Pan to mid (50)
    'ZZNL000;',  # Sets VFO A Wide Noise Blanker (WNB) Level to 0
    'ZZNR0;',  # Sets Slice Noise Reduction (NR) State to off
    'ZZPC000;',  # Sets RF Power Drive Level to 0
    'ZZRC;',  # Clear Slice A RIT Frequency
    'ZZRT0;',  # Sets or reads VFO A RIT State off
]
"""_BAND_DATA
   a dictionary with the key being a string representing the band.
   if the value only contains 2 values, those values represent the start frequencey and end
   frequency of the band.  Intermediat frequencies for noise measurement are automatically generated

   if more than 2 frequencies, then only those frequences are measured (60m band is channalized)
"""
_BAND_DATA = {'80': (3_500_000, 4_000_000,),
              '60': (5_330_500, 5_346_500, 5_357_000, 5_371_500, 5_403_500,),
              '40': (7_000_000, 7_300_000,),
              '30': (10_100_000, 10_150_000,),
              '20': (14_000_000, 14_350_000,),
              '17': (18_068_000, 18_168_000,),
              '15': (21_025_000, 21_450_000,),
              '12': (24_890_000, 24_990_000,),
              '10': (28_000_000, 29_700_000,),
              '6': (50_000_000, 54_000_000,),
              }

# """RESTORE_FLEX
# storage for the saved state of the flex, executing these commands will restor the flex
# to its saved state

# I do not think this is being used
# """
# RESTORE_FLEX = {
# restore freq, mode, dsp agc wnb
# }
GET_SMETER_PROTO: List[Tuple[Any, Any]] = [
    ('wait0.25', None, ),
    ('ZZSM;', smeter, ),
]

GET_DATA = [
    # GET_DATA
    # list of tuples that include commands to the radio and handling processing of the return.
    # Also the wait provide delays between commands in decimal seconds
    ('wait0.5', None, ),
    ('ZZSM;', smeter, ),
    ('wait0.25', None, ),
    ('ZZSM;', smeter, ),
    ('wait0.25', None, ),
    ('ZZSM;', smeter, ),
    ('wait0.25', None, ),
    ('ZZSM;', smeter, ),

]

GET_FAST_DATA = [
    # GET_DATA
    # list of tuples that include commands to the radio and handling processing of the return.
    # Also the wait provide delays between commands in decimal seconds
    ('wait0.125', None, ),
    ('ZZSM;', smeter, ),
    ('wait0.05', None, ),
    ('ZZSM;', smeter, ),
    ('wait0.05', None, ),
    ('ZZSM;', smeter, ),
    ('wait0.05', None, ),
    ('ZZSM;', smeter, ),

]

_NUM_BAND_SAMPLE = 10  # number of samples in band *3
_SAMPLE_SPREAD = 1500  # +- samples from above


class BandPrams:
    """BandPrams(item[str, Tuple[int,...]])

    the item is an item from _BAND_DATA
    The bands are disabled by default and should be enabled using
    postproc.enable_bands

    initilization generates the frequences for measurement responsive to if the band is channeled or not.
    it also generates the flex command to change to the specified frequencies.

    need to make test
    """

    def __init__(self, item: Mapping[str, Tuple[int, ...]]):

        #_itml = list(item)
        self.bandid = item[0]
        bfreql = list(item[1])
        if len(bfreql) < 2:
            raise ValueError
        lowend = bfreql[0]
        highend = bfreql[-1]
        self._channeled: bool = None
        self._enable: bool = False
        self._freqs: List[int] = []
        if len(bfreql) == 2:
            widbandinc = (highend - lowend) / _NUM_BAND_SAMPLE
            self._freqs = [int(lowend + i *
                               widbandinc) for i in range(_NUM_BAND_SAMPLE + 1)]
            freqs1 = []
            for f in self._freqs:
                freqs1.extend([int(f - _SAMPLE_SPREAD),
                               int(f), int(f + _SAMPLE_SPREAD)])

            # f'ZZFA{int(a) :011d};'
            self._sample_freqcmdl = [f'ZZFA{int(fval) :011d};' for fval in freqs1]
            self._channeled = False
        else:
            self._freqs = bfreql[:]
            self._sample_freqcmdl = [f'ZZFA{int(fval) :011d};' for fval in self._freqs]
            self._channeled = True

    def __str__(self) -> str:
        return f'band:{self.bandid}, enabled: {self._enable}, chan: {self._channeled}, {self._freqs}'

    def __repr__(self) -> str:
        return f'BandPrams: {str(self)}'

    def get_freq_cmds(self) -> Tuple[str, ...]:
        """get_freq_cmds()

           returns a tuple of strings that are the flex commands to switch to a particualr frequency
        """
        result: Tuple[str, ...] = tuple(self._sample_freqcmdl[:])
        return result

    def is_enabled(self):
        return self._enable


BANDS: Dict[str, BandPrams] = {}
"""BANDS
   a dictionary of string bandids ('20') with a BandPrams value
"""
for i in _BAND_DATA.items():  # setup BANDS
    BANDS[i[0]] = BandPrams(i)


def enable_bands(bndids: Sequence[str], val: bool = True) -> int:
    """enable_bands(['40','20'], val= True):

    enables or disables which bands are to be checked.
    returns the number of bands changed by the command

    non-existant band ids are ignored
    """
    keyset = BANDS.keys()
    result = 0
    for k in bndids:
        if k in keyset:
            b = BANDS[k]
            if b._enable ^ val:
                b._enable = val
                result += 1

    return result


enable_bands(['30', '40', '20'])

# class PostProc():
# """PostProc()

# """

# def __init__(self, userI, testdata=None, testing=False):

#self._ui = userI
#self._td = None
# if testdata:
# if isinstance(testdata, list):
#self._td = testdata
# self._td.reverse()
# else:
#assert "illegal testdata type"

# def __str__(self):
# return '[{}, {}]'.format(self._ui, self._td)
# return f'[{self._ui}, {self._td}'

# def __repr__(self):
# return f'[PostProc: {str(self)}]'


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
    THE_LOGGER.info('postproc executed as main')

    try:
        main()
        normalexit = True
    except(Exception, KeyboardInterrupt) as exc:
        print(exc)
        normalexit = False

    finally:
        if normalexit:
            sys.exit('normal exit')
        else:
            sys.exit('error exit')

