#!/usr/bin/env python3.7
"""
Test file for need
"""

# import datetime
##from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque
from typing import Any, Tuple, List, Dict, Set


##import statistics
import threading
from concurrent.futures import ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED
from time import monotonic
from time import sleep as Sleep
from collections import deque, namedtuple
import time
import concurrent
from queue import Empty as QEmpty, Full as QFull
import multiprocessing as mp
import unittest
from multiprocessing import freeze_support
from typing import Any, List, Dict, Tuple
import pickle
from statistics import fmean

import context
import qdatainfo
from trackermain import SepDataTup
from nfresult import NFResult

from queuesandevents import RESET_STOP_EVENTS, RESET_QS, ARG_KEYS
from queuesandevents import QUEUES, CTX, STOP_EVENTS
from queuesandevents import QUEUE_KEYS as QK
from queuesandevents import Enables as ENABLES
from queuesandevents import POSSIBLE_F_TKEYS as FK
from queuesandevents import STOP_EVENT_KEYS as SEK
import trackermain
from deck import Deck

from trackermain import _thread_template, Threadargs, _qcpy, genargs, dataQ_reader

defineownTL: bool = False
TL = None

try:
    from trackermain import TML as TL
except ImportError as ie:
    defineownTL = True

if defineownTL:
    TL = threading.local()

del defineownTL

# Testing queue to gather info
TESTQ = CTX.JoinableQueue(maxsize=10000)
TESTOUTQ = CTX.JoinableQueue(maxsize=300)


#SepDataTup = namedtuple('SepDataTup', ['strr', 'nfq', 'lwq', 'other'])
#Stopeventkey = namedtuple('Stopeventkey', ['ad', 't', 'da', 'db'])


class TestTrackerDQR(unittest.TestCase):

    """TestTrackermain

    """

    def setUp(self):
        """setUp()

        """
        RESET_STOP_EVENTS()
        RESET_QS()
        self.QUEUEDDATA = []
        with open('dadata3hr.pickle', 'rb') as f2:  # should contain duplicate records
            try:
                self.QUEUEDDATA = pickle.load(f2)
            except Exception as ex:
                a = 0
        self.assertEqual(112, len(self.QUEUEDDATA))

    def tearDown(self):
        """tearDown()

        """
        pass

    @classmethod
    def setUpClass(cls):
        """setUpClass()

        """
        QUEUES[QK.dQ] = CTX.JoinableQueue(maxsize=200)
        QUEUES[QK.dpQ] = CTX.JoinableQueue(maxsize=200)
        QUEUES[QK.dbQ] = CTX.JoinableQueue(maxsize=200)

    @classmethod
    def tearDownClass(cls):
        """tearDownClass()

        """
        RESET_QS()
        for q in QUEUES.values():
            q.close()

    def testA000_dataQpickleread(self):
        import pickle
        queddata: List[Any]

        with open('dadata3hr.pickle', 'rb') as f2:  # should contain duplicate records
            try:
                queddata = pickle.load(f2)
            except Exception as ex:
                a = 0
        self.assertEqual(112, len(queddata))
        deck = Deck(500)
        deck.extend(queddata)
        self.assertEqual(112, len(deck))
        cpyqd: List[Any] = deck.deck2lst()
        self.assertEqual(112, len(cpyqd))
        for c, o in zip(cpyqd, queddata):
            self.assertEqual(c, o)

        sepstup: SepDataTup = trackermain.seperate_data(deck.deck2lst())
        self.assertFalse(sepstup.strr)
        self.assertEqual(60, len(sepstup.nfq))
        self.assertEqual(52, len(sepstup.lwq))
        self.assertFalse(sepstup.other)

    def testA0001_dataQ(self):

        queddata: List[Any] = self.QUEUEDDATA[:]
        sepstup: SepDataTup = trackermain.seperate_data(queddata)
        nfqlen = len(sepstup.nfq)
        temp1: List[Tuple[NFResult, NFResult]] = []
        temsort = sepstup.nfq[:]

        def myfun(a: ) -> float:
            return
        aa: List[NFQ] = [] need to sort this stuff
        for _i in range(1, nfqlen):
            temp1.append((sepstup.nfq[_i - 1].get(), sepstup.nfq[_i].get()))

        temp2: List[Tuple[NFResult, NFResult]] = [
            x for x in temp1 if x[0] != x[1]]
        a = 0
        pass


if __name__ == '__main__':

    freeze_support()
    unittest.main()
