#!/usr/bin/env python3

import sys
import os
import random
from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Mapping, List
#from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque, Iterable
import logging
import logging.handlers
import datetime
import pickle
from time import sleep as Sleep
from time import monotonic
from queue import Empty as QEmpty
import multiprocessing as mp
from nfresult import NFResult

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/quicktestsdeleteme'


def main():

    indata = []
    with open('./tests/nfqlistdata.pickle', 'rb') as jso:
        indata = pickle.load(jso)

    sindata = indata[:]
    count = 0
    for a, b in zip(indata, sindata):
        if a != b:
            break
        count += 1

    sindata = random.sample(indata, len(indata))
    count = 0
    for a, b in zip(indata, sindata):
        if a != b:
            break
        count += 1
    sindata.sort()
    count = 0
    for a, b in zip(indata, sindata):
        if a != b:
            break
        count += 1
    #
    # above shows that sorting NFQ works

    unwrapped: List[NFResult] = [npq.get() for npq in indata]

    savedunwrapped: List[NFResult] = []

    with open('./tests/nfrlistdata.pickle', 'rb') as jso:
        savedunwrapped = pickle.load(jso)

    reads: List[SMeterAvg] = []
    for nfr in unwrapped:
        reads.extend(nfr.readings)

    savedreads: List[SMeterAvg] = []
    with open('smavflistdata.pickle', 'rb') as jso:
        savedreads = pickle.load(jso)

    #up0: NFResult = unpacked[0]
    #outdata = []
    # with open('nfqlistdata.pickle', 'rb') as jsi:
        #outdata = pickle.load(jsi)

    #brlst: List[Bandreadings] = []
    # for nfq in outdata:
        #br: Bandreadings = nfq.get()
        # brlst.append(br)

    a = indata[0]
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

    # THE_LOGGER.setLevel(logging.CRITICAL)
    # THE_LOGGER.setLevel(logging.ERROR)
    # THE_LOGGER.setLevel(logging.WARNING)
    # THE_LOGGER.setLevel(logging.INFO)
    THE_LOGGER.setLevel(logging.DEBUG)
    # THE_LOGGER.setLevel(logging.NOTSET)

    THE_LOGGER.addHandler(LF_HANDLER)
    THE_LOGGER.addHandler(LC_HANDLER)
    THE_LOGGER.info('quecktestsdeleteme executed as main')

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
