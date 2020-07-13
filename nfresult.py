#!/usr/bin/env python3

"""  TBD """

import sys
import os
#from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict
from typing import List
import logging
import logging.handlers
#import datetime

import time  # can use this instead of datetime as it is only used to get text
#from queue import Empty as QEmpty
#import multiprocessing as mp
## from statistics import mean
## import mysql.connector as mariadb
#from userinput import UserInput
## from smeter import SMeter, _SREAD
from bandreadings import Bandreadings
from smeteravg import SMeterAvg

#from flex import Flex
##import dbtools
#import postproc
#import noisefloor
#from postproc import BANDS, BandPrams
#from qdatainfo import NFQ
#from trackermain import QUEUES, STOP_EVENTS, CTX


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/nfresult'


class NFResult:
    """NFResult()

    holds the result from running _oneloopallbands()
    """

    def __init__(self, ):
        self.starttime: str = 'Not Started'
        self.endtime: str = 'Not Ended'
        self.readings: List[SMeterAvg] = []
        self._started: bool = False
        self._ended: bool = False

    def __str__(self):
        if self._started and self._ended:
            readinginfo = []
            readinginfo = [(r.band,
                            r.signal_st.get('sl'),
                            r.signal_st.get('stddv')) for r in self.readings if r is not None]
            readinglst: [str] = [f'NoiseFloor reading', f'{self.starttime}']
            for _ in readinginfo:
                readinglst.append(f'    b:{_[0]}, {_[1]}, {_[2] :.2f}')

            readinglst.append(f'{self.endtime}')
            result = '\n'.join(readinglst)
            return result

        if self._started:
            return f'band readings started at {self.starttime}'
        return 'Not Started'

    def __repr__(self):
        text: str = None
        if self._started and self._ended:
            lines: List[str] = []
            for r in self.readings:
                if r is None:
                    continue
                reads: List[str] = [
                    f'b:{r.band}, {r.signal_st.get("sl")},',
                    f'stddv:{r.signal_st["stddv"] :.3f}, adBm: {r.dBm["adBm"] :.3f}, mdBm: {r.dBm["adBm"] :.3f}'
                ]
                lines.append(' '.join(reads))
            out: str = '\n'.join(lines)

            text = f'NFResult: st:{self.starttime}, et:{self.endtime}\n{out}'
            return text
        elif self._started:
            return f'NFResult started at {self.starttime}'

        return 'NFResult: Not Started'

    def __eq__(self, other):
        """__eq__(self,other)

        Equality does not compare the date/time values, only the
        condition of started and ended and the band, sl, and stddv
        """
        if self is other:
            return True

        if (not (isinstance(self, NFResult) and isinstance(other, NFResult))) or len(self.readings) != len(other.readings) or self._ended ^ other._ended:
            return False
        if (len(self.readings) + len(other.readings) == 0):
            return True

        sreadings = [(
            r.band,
            r.signal_st.get('sl'),
            r.signal_st.get('stddv'),
        )
            for r in self.readings if r is not None and isinstance(r, SMeterAvg)]
        oreadings = [(
            r.band,
            r.signal_st.get('sl'),
            r.signal_st.get('stddv'),
        )
            for r in other.readings if r is not None and isinstance(r, SMeterAvg)]

        if len(oreadings) != len(sreadings):
            return False

        one2one = zip(sreadings, oreadings)
        result: bool = True
        for s, o in one2one:
            result = result and s[0] == o[0] and s[1] == o[1]
            dif = s[2] - o[2]
            # if dif < 0.0:
            #dif = o[2] - s[2]
            dif = dif if dif >= 0 else -dif
            result = result and dif < 0.3
            if not result:
                break
        return result

    def __ne__(self, other):
        return not self.__eq__(other)

    # def __lt__(self, other):
        # pass

    # def __gt__(self, other):
        # pass

    # def __le__(self, other):
        # pass

    # def __ge__(self, other):
        # pass

    def start(self, strftimein: str = None):
        if not self._started:
            if not strftimein:
                self.starttime = time.strftime(
                    "%b %d %Y %H:%M:%S", time.localtime())
            else:
                self.starttime = strftimein
            self._started = True

    def end(self, brs: List[SMeterAvg], strftimein: str = None):
        if self._started and not self._ended:
            if not strftimein:
                self.endtime = time.strftime(
                    "%b %d %Y %H:%M:%S", time.localtime())
            else:
                self.endtime = strftimein

            # self.readings:List[SMeterAvg] = []
            # br: SMeterAvg = None
            self.readings = brs[:]
            self._ended = True

    def completed(self) -> bool:
        return self._started and self._ended

    def gen_sql(self):
        pass


def NFFactory(oldnfr: NFResult) -> NFResult:
    result: NFResult = NFResult()
    result._ended = oldnfr['_ended']
    result._started = oldnfr['_started']
    result.readings = oldnfr['readings'][:]
    result.starttime = oldnfr['starttime']
    result.endtime = oldnfr['endtime']
    return result


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
    THE_LOGGER.info('nfresult executed as main')
    # LOGGER.setLevel(logging.DEBUG)

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
