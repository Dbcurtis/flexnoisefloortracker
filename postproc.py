#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import os
import logging
import logging.handlers
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
    resulttup[1] is

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
    sm = SMeter(arg)
    return sm


INITIALZE_FLEX = [
    # """ commands to set the radio to an initial condition. To be used after
    # the current radio state is saved by savstate = flex.save_current_state()
    # and the flex restored via flex.restore_state(savestate)
    # """
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

FREQUENCIES = ['{:011}'.format(_) for _ in [
    # frequences in each band that will get sampled
    # one or more may be changed if the standard deveation between the
    # frequencies is to large.
    3_500_000, 3_700_000, 4_000_000,
    7_000_000, 7_150_000, 7_300_000,
    10_100_000, 10_075_000, 10_150_055,
    14_000_000, 14_175_000, 14_373_000,
    # 14_000_000, 14_173_643, 14_350_000,
]]

RESTORE_FLEX = {
    # restore freq, mode, dsp agc wnb
}


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


class PostProc():
    """PostProc()

    """

    def __init__(self, userI, testdata=None, testing=False):
        _s = self
        self._ui = userI
        self._td = None
        if testdata:
            if isinstance(testdata, list):
                self._td = testdata
                self._td.reverse()
            else:
                assert "illegal testdata type"

    def __str__(self):
        return '[{}, {}]'.format(self._ui, self._td)

    def __repr__(self):
        return '[PostProc: {}, {}]'.format(self._ui, self._td)


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
