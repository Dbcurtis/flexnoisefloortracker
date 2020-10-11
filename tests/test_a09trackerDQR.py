#!/usr/bin/env python3.7
"""
Test file for need
"""

# import datetime
# from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque
from typing import Any, Tuple, List, Dict, Set, Deque


# import statistics
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

from qdatainfo import Qdatainfo, DataQ, LWQ, NFQ, DbQ, DpQ
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


# SepDataTup = namedtuple('SepDataTup', ['strr', 'nfq', 'lwq', 'other'])
# Stopeventkey = namedtuple('Stopeventkey', ['ad', 't', 'da', 'db'])


def removeadjdups(lstin: List[Qdatainfo]) -> List[Qdatainfo]:
    return _removeadjdups(lstin)


def _removeadjdups(lstin: List[Any], sfn=lambda a, b: a != b) -> List[Any]:
    """_removedadjdups(lstin: List[Any], sfn=lambda a, b: a != b) ->List[Any]

    lstin is a list of Any
    sfn defaults to a lambda (a,b) that returns a!=b

    """
    tempdeque = deque(lstin)
    resultdq = deque()
    cur: Any = tempdeque.popleft()  # use the first item as my current item
    resultdq.append(cur)  # and put it on the results
    try:
        while True:
            neew = tempdeque.popleft()  # keep popping till out of pops
            if sfn(cur, neew):  # cur != neew:
                cur = neew  # different so make neew cur
                resultdq.append(neew)  # and save neew
    except:
        pass

    return list(resultdq)


class TestTrackerDQR(unittest.TestCase):

    """TestTrackermain

    """

    def setUp(self):
        """setUp()

        """
        RESET_STOP_EVENTS()
        RESET_QS()
        self.QUEUEDDATA = []
        with open('dadata_03_15_dups.pickle', 'rb') as f2:  # should contain duplicate records
            try:
                self.QUEUEDDATA = pickle.load(f2)
            except Exception as ex:
                raise ex
        self.assertEqual(121, len(self.QUEUEDDATA))

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
        """testA000_dataQpickleread()

        Just check that I can read a picked file with a mixture of NFQ, LWQ, Text, and Other entries
        and be able to separate them out.

        This checks that the test setup read works correctly

        Also does the first check on trackermain.seperate_data

        """
        import pickle
        queddata: List[Any]

        with open('dadata_03_15_dups.pickle', 'rb') as f2:  # should contain duplicate records
            try:
                queddata = pickle.load(f2)
            except Exception as ex:
                raise ex
        self.assertEqual(121, len(queddata))
        deck = Deck(500)
        deck.extend(queddata)
        self.assertEqual(121, len(deck))
        cpyqd: List[Any] = deck.deck2lst()
        self.assertEqual(121, len(cpyqd))
        for c, o in zip(cpyqd, queddata):
            self.assertEqual(c, o)

        deck.append('text1')
        deck.append('text2')
        deck.append({'d': 1})
        self.assertEqual(124, len(deck))
        sepstup: SepDataTup = trackermain.seperate_data(deck.deck2lst())
        self.assertEqual(2, len(sepstup.strr))
        self.assertEqual(65, len(sepstup.nfq))
        self.assertEqual(56, len(sepstup.lwq))
        self.assertEqual(1, len(sepstup.other))

    def testA001_dataQ(self):
        """testA001_dataQ()

        Check that sorting the queued data operates as expected.

        show I can append the list to itsself, sort, remove duplicates and have the origninal list back
        """

        queddata: List[Any] = self.QUEUEDDATA[:]
        self.assertEqual(121, len(queddata))
        self.assertNotEqual(str(queddata[0]), str(queddata[1]))
        queddata.extend(self.QUEUEDDATA[:])  # duplicate the list

        self.assertEqual(242, len(queddata))
        # shows the list is not sorted
        self.assertNotEqual(str(queddata[0]), str(queddata[1]))
        queddata.sort()  # timnestamp order
        # shows the list is sorted correctly
        self.assertEqual(str(queddata[0]), str(queddata[1]))
        #aaa: List[Any] = _removeadjdups(queddata)
        self.assertEqual(121, len(_removeadjdups(queddata)))

        queddata = self.QUEUEDDATA[:]

        queddata.sort()  # sorts by time queued

        sepstup: SepDataTup = trackermain.seperate_data(queddata)
        self.assertEqual(65, len(sepstup.nfq))
        self.assertEqual(56, len(sepstup.lwq))
        lwqlstcleaned: List[LWQ] = sepstup.lwq[:]
        lwqlstcleaned.sort()

        nfqlstdirty: List[NFQ] = sepstup.nfq[:]
        nfqlstdirty.sort()
        # checks that sepstup.nfq is sorted
        self.assertTrue(sepstup.nfq == nfqlstdirty)
        nfqnotimedup = removeadjdups(nfqlstdirty)
        self.assertTrue(nfqnotimedup == nfqlstdirty)

        lwqlstdirty: List[LWQ] = sepstup.lwq[:]
        lwqlstdirty.sort()
        self.assertTrue(sepstup.lwq == lwqlstdirty)
        lwqnotimedup = removeadjdups(lwqlstdirty)
        self.assertTrue(lwqnotimedup == lwqlstdirty)

        nflst: List[NFResult] = [x.get() for x in sepstup.nfq]
        self.assertEqual(52, len(_removeadjdups(nflst)))

        lwlst: List[str] = [x.get() for x in sepstup.lwq]
        self.assertEqual(19, len(_removeadjdups(lwlst)))

    def testA002_dataQ(self):
        """testA002_dataQ()


        """
        queddata: List[Any] = self.QUEUEDDATA[:]
        queddata.sort()  # sorts by time queued

        def valid_check(nnfr: NFResult) -> bool:
            """valid_check(nnfr: NFResult) -> bool

            Checks if a NFResult is valid. Invalid ones have .signal_st['sl] == 'sE'

            """
            result: bool = True
            for _ in nnfr.readings:
                aa = _.signal_st['sl']
                if 'sE' == aa:
                    result = False
                    break
            return result

        def reducenfq(arg: List[NFQ], sfn1=lambda a, b: a == b, sfn2=lambda a, b: a != b) -> List[NFQ]:
            """reducenfq(arg: List[NFQ], sfn1=lambda a, b: a == b, sfn2=lambda a, b: a != b) -> List[NFQ]:

            """
            deck: Deque[NFQ] = deque(arg)

            curnfq: NFQ = deck.popleft()
            while True:  # make curnfq first valid NFQ
                nnfr: NFResult = curnfq.get()
                if valid_check(nnfr):
                    break
                curnfq = deck.popleft()

            resultdq: Deque[NFQ] = deque()
            resultdq.append(curnfq)

            try:
                while True:
                    newnfq: NFQ = deck.popleft()
                    if sfn1(curnfq, newnfq):  # cur == neew:
                        continue
                    nnfr: NFResult = newnfq.get()
                    if valid_check(nnfr):
                        difnft: bool = sfn2(curnfq.get(), nnfr)
                        if difnft:
                            curnfq = newnfq
                            resultdq.append(newnfq)

            except:
                pass
            return resultdq

        def reducelwq(arg: List[LWQ]) -> List[LWQ]:
            """reducelwq(arg: List[LWQ]) -> List[LWQ]:

            """
            deck: Deque[LWQ] = deque(arg)
            resultdq = deque()
            curlwq: LWQ = deck.popleft()
            resultdq.append(curlwq)
            try:
                while True:
                    newlwq: LWQ = deck.popleft()
                    #diflwq: bool = curlwq.get() != newlwq.get()
                    if curlwq.get() != newlwq.get():
                        curlwq = newlwq
                        resultdq.append(newlwq)

            except:
                pass
            return resultdq

        sepstup: SepDataTup = trackermain.seperate_data(queddata)
        ad = reducenfq(sepstup.nfq)
        self.assertEqual(32, (len(ad)))
        bd = reducelwq(sepstup.lwq)
        self.assertEqual(19, (len(bd)))
        ad.extend(bd)
        cl = list(ad)
        cl.sort()
        # skip till the first lwq entry which holds the reference date.
        while not isinstance(cl[0], LWQ):
            cl.pop(0)

        sepstup1: SepDataTup = trackermain.seperate_data(cl)
        self.assertEqual(19, len(sepstup1.lwq))
        self.assertEqual(32, len(sepstup1.nfq))


if __name__ == '__main__':

    freeze_support()
    unittest.main()
