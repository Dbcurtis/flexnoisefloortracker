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
from collections import deque
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

from queuesandevents import QUEUES, CTX, STOP_EVENTS,RESET_STOP_EVENTS
from queuesandevents import RESET_QS as reset_queues
from queuesandevents import QUEUE_KEYS as QK
from queuesandevents import ARG_KEYS as AK
from queuesandevents import Enables as ENABLES
from queuesandevents import POSSIBLE_F_TKEYS as FK
from queuesandevents import STOP_EVENT_KEYS as SEK
import trackermain
from deck import Deck

from trackermain import _thread_template, Threadargs, _qcpy, genargs

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


def cleartestq():
    while True:
        try:
            TESTQ.get_nowait()
            TESTQ.task_done()
        except QEmpty:
            break

    while True:
        try:
            TESTOUTQ.get_nowait()
            TESTOUTQ.task_done()
        except QEmpty:
            break


def marktime(dly=2.5, cnt=6):
    for _ in range(cnt):
        print('|', end='')
        time.sleep(dly)
    print('', end=None)


def clearstopevents():
    #[e.clear() for e in STOP_EVENTS.values()]
    # for e in stopevents.values():
    # e.clear()
    RESET_STOP_EVENTS()


def myprint(st):  # used to print output, and/or put the output on the TESTQ
    #print(st)
    TESTQ.put(st)


def breakwait(barrier):
    barrier.wait()
    myprint('breakwait started')


def bwdone(f):
    myprint('breakwait done')


def _genTdif(aa: List[float]) -> List[Tuple[float, ...]]:
    """_genTdif(aa: List[float])

    generates the differences between adjacent times in aa
    for each pair, returns a tupal of starttime, endtime, differenc

    """
    result: List[Tuple[float, ...]] = []
    for _ in range(1, len(aa)):
        result.append((aa[_ - 1], aa[_], aa[_] - aa[_ - 1]))
    return result


def _genTimes(aa: List[str]) -> List[float]:
    """_genTimes(aa: List[str])

    returns a list of float that have the float value of the t=value string

    """
    result: List[float] = []
    for _v in aa:
        if 't=' in _v:
            _w = _v.split('t=', 1)
            _wf = float(_w[1])
            result.append(_wf)
    return result


def _gentimedict(cdi: Dict[str, float]) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for k, v in cdi.items():
        tms: List[float] = _genTimes(v)
        difs: List[Tuple[float, ...]] = _genTdif(tms)
        result[k] = difs
    return result


def _trimstartend(dic: Dict[str, float], keys: List[str]):
    """_trimstartend(dic: Dict[str, float], keys: List[str]

    removes the first and last entry of the list value from dic for the selected key
    """
    for k in keys:
        if k not in dic.keys():
            continue
        dic[k] = dic[k][1:-1]


def _checktiming(d1: Dict[str, float], d2: Dict[str, float]) -> bool:
    result = True
    tolerance = 0.7
    for k in d1.keys():
        diff = abs(d1[k] - d2[k])
        result = result and (diff < tolerance)
    return result


def _avragedict(timeddic) -> Dict[str, float]:
    result = {}
    for k, v in timeddic.items():
        kk = [_[2] for _ in v]
        if not kk:
            result[k] = -1
            continue
        s = sum(kk)
        result[k] = round(s / len(kk), 2)

    returnresult = {k: result[k]
                    for k in result if result[k] > 0}
    return returnresult


#def startThreads(tpex, bollst, barrier, stopevents, queues):
    #"""startThreads(tpex, bollst, barrier, stopevents, queues)

     #starts the weather, noise, transfer, dataagragator, and dbwriter threads responsive to the bollst boolena array

     #tpex is the executor
     #bollst is the boolean list specifying which threads to start
     #barrier is the barrier to wait on for all the selected threads to start on
     #stopevents is the dict of stop events specifying which event the thread is to stop resonive to.
     #queues is the dict of queues.

     #deprecated I think
    #"""

    #threadinfo = {
        #'weather': (bollst.w, barrier, stopevents['acquireData'], queues,),
        #'noise': (bollst.n, barrier, stopevents['acquireData'], queues,),
        #'transfer': (bollst.t, barrier, stopevents['trans'], queues,),
        #'dataagragator': (bollst.da, barrier, stopevents['agra'], queues,),
        #'dbwriter': (bollst.db, barrier, stopevents['dbwrite'], queues,),
    #}

    #futures = {
        ## gets weather data
        #'weather': tpex.submit(trackermain.timed_work, threadinfo['weather'], 5, Get_LW),
        ## gets banddata data
        #'noise': tpex.submit(trackermain.timed_work, threadinfo['noise'], 5, Get_NF),
        ## reads the dataQ and sends to the data processing queue dpq
        #'transfer': tpex.submit(trackermain.dataQ_reader, threadinfo['transfer']),
        ## looks at the data and generates the approprate sql to send to dbwriter
        #'dataagragator': tpex.submit(trackermain.dataaggrator, threadinfo['dataagragator'], debugfn=aggrfn),
        ## reads the database Q and writes it to the database
        #'dbwriter': tpex.submit(trackermain.dbQ_writer, threadinfo['dbwriter'], debugfn=dbconsum)

    #}
    #return futures


def dbconsum(thread_info):
    """dbconsum(thread_info)

    thread_info is (execute, barrier, stop_event, queues,)

    Test function to remove everything from the dbQ
    """
    if not thread_info[0]:
        return
    print('dbconsum at barrier\n', end="")
    thread_info[1].wait()
    print('dbconsum starting\n', end='')

    stop_event = thread_info[2]


def aggrfn(thread_info):
    """aggrfn(thread_info)

    thread_info is (execute, barrier, stop_event, queues,)

    Test function for dataaggrator in trackermain.py

    """
    if not thread_info[0]:
        return
    print('aggrfn at barrier\n', end="")
    thread_info[1].wait()
    print('aggrfn starting\n', end='')
    dpQ_IN = thread_info[3]['dpQ']
    dbQ_OUT = thread_info[3]['dbQ']
    deck = Deck(100)
    stop_event = thread_info[2]
    doit = True
    while doit:

        deck.q2deck(dpQ_IN, False, 5)
        time.sleep(0.001)  # provide oppertunity to switch threads

        notstop = not stop_event.is_set()
        while notstop or len(deck) > 0:
            if len(deck) == 0:
                break
            deck.deck2q(dbQ_OUT, dpQ_IN, lambda a: a * 10)
            if stop_event.is_set() and dpQ_IN.empty():
                break

        doit = not stop_event.wait(6)

    for _ in range(10):  # get any late queued info
        deck.q2deck(dpQ_IN, False, 0.5)
        while True:
            try:  # empty deck to dbQ_OUT
                deck.deck2q(dbQ_OUT, dpQ_IN, lambda a: a * 10)
            except QEmpty:
                break
            except IndexError:
                break
            except QFull:
                pendingwrite = deck.popleft()
                time.sleep(0.001)

    print('aggrfn ended\n', end="")
    return []


def Get_LW(q_out):
    """Get_LW(q_out)

    debug the local weather handling

    """
    for i in range(5):
        q_out.put(i)
        time.sleep(0.25)


def Get_NF(q_out):
    """Get_NF(q_out)

    debug the noise handling

    """
    for i in range(5):
        q_out.put(i * 10.0)
        time.sleep(0.3)


def do1argnull(arg):
    """do1argnull(arg)

    do nothing
    """
    pass


class TestTrackermain(unittest.TestCase):
    global clsa
    clsa = None
    """TestTrackermain

    """

    def setUp(self):
        """setUp()

        """
        clearstopevents()
        # reset queues
        QUEUES[QK.dQ] = CTX.JoinableQueue(maxsize=100)
        QUEUES[QK.dpQ] = CTX.JoinableQueue(maxsize=100)
        QUEUES[QK.dbQ] = CTX.JoinableQueue(maxsize=100)

    def tearDown(self):
        """tearDown()

        """
        pass

    @classmethod
    def setUpClass(cls):
        """setUpClass()

        """

        pass

    @classmethod
    def tearDownClass(cls):
        """tearDownClass()

        """
        pass

    def testA000_dataQpickleread(self):
        import pickle
        queddata:List[Any]

        with open('dadata3hour.pickle', 'rb') as f2:  #should contain duplicate records
            try:
                queddata = pickle.load(f2)
            except Exception as ex:
                a = 0
        self.assertEqual(112, len(queddata))
        lwqlst:list[LWQ] = [e for e in queddata if repr(e).startswith('LWQ')]
        nfqlst:list[NFQ] = [e for e in queddata if repr(e).startswith('NFQ')]

        def kk(a1,a0) -> float:
            t1 = a1.utctime
            ts1 = a1.utctime.timestamp()
            t0=a0.utctime
            ts0=a0.utctime.timestamp()
            return ts1-ts0

        nfqtimedifs = [kk(nfqlst[i],nfqlst[i-1])  for i in range(1,len(nfqlst))]
        lwqtimedifs = [kk(lwqlst[i],lwqlst[i-1])  for i in range(1,len(lwqlst))]
        from statistics import mean, median, stdev

        # mean and med for dadata3hr.pickle is about 180 st <0.05
        self.assertAlmostEqual(180.00, mean(nfqtimedifs),delta=0.1)
        self.assertAlmostEqual(180.00,median(nfqtimedifs),delta=0.1)
        self.assertAlmostEqual(0.114,stdev(nfqtimedifs),delta=0.005)

        # mean and med for dadata3hr.pickle is about 210 st <0.05
        self.assertAlmostEqual(209.99, mean(lwqtimedifs),delta=0.1)
        self.assertAlmostEqual(209.99,median(lwqtimedifs),delta=0.1)
        self.assertAlmostEqual(1.605,stdev(lwqtimedifs),delta = 0.03)
        lw0=lwqlst[0].get()
        expected = 'INSERT INTO weather SET Sunset = 1594673244000000, Sunrise = 1594619212000000, RecDT = 1594651403000000, Humidity = 34.0, TempF = 83.12, WindS = 6.9, WindD = 220, WindG = 0.0'
        self.assertEqual(expected, str(lw0))
        nf0=nfqlst[0].get()
        expected = 'NoiseFloor reading\nJul 13 2020 14:47:55\n    b:40, S6, 1.25\n    b:30, S5, 0.46\n    b:20, S3, 0.49\nJul 13 2020 14:49:01'
        self.assertEqual(expected, str(nf0))
        expected = 'NFResult: st:Jul 13 2020 14:47:55, et:Jul 13 2020 14:49:01\nb:40, S6, stddv:1.247, adBm: -86.485, mdBm: -86.485\nb:30, S5, stddv:0.456, adBm: -94.516, mdBm: -94.516\nb:20, S3, stddv:0.492, adBm: -104.083, mdBm: -104.083'
        self.assertEqual(expected, repr(nf0))
        nfqtstlst = []

        #_last_band_readings=nfqlst[0]
        #_last_w_readings = lwqlst[0]
        nfqtstlst=nfqlst[0:1]
        lwqtstlst=lwqlst[0:1]


        #def removedups(nfresult):
            #if (not _last_band_readings) or nfresult != _last_band_readings:  # remove close readings
                        #_last_band_readings = nfresult
                        #nfqtstlst.append(nfresult)

        #self.assertFalse( nfqlst[0].get().__eq__( nfqlst[1].get()))
        #self.assertFalse(nfqlst[0].get() ==  nfqlst[1].get())
        #self.assertTrue( nfqlst[0].get().__ne__( nfqlst[1].get()))
        #self.assertTrue(nfqlst[0].get() !=  nfqlst[1].get())
        self.assertEqual(60,len(nfqlst))
        for i in range(1,len(nfqlst)):
            if nfqlst[i-1].get()!=nfqlst[i].get():
                nfqtstlst.append(nfqlst[i])
        self.assertEqual(40,len(nfqtstlst))


        self.assertEqual(52,len(lwqlst))
        for i in range(1,len(lwqlst)):
            if lwqlst[i-1].get()!=lwqlst[i].get():
                #print(lwqlst[i].get())
                lwqtstlst.append(lwqlst[i])

        self.assertEqual(19,len(lwqtstlst))


    def testA001_qcpy(self):

        INQ = CTX.JoinableQueue(maxsize=100)
        OUTQ = CTX.JoinableQueue(maxsize=100)
        deck = Deck(10)
        counts = (0, 0,)

        def emptyout():
            try:
                while True:
                    OUTQ.get(True, 3)
            except:
                pass

        #args = (True, None, STOP_EVENTS['agra'], QUEUES, 'testqcpy', 0.5,)
        arg = Threadargs(
            True, None, STOP_EVENTS[SEK.da], QUEUES, 'testqcpy', 0.5, doit=None)
        counts = _qcpy(deck, INQ, OUTQ, arg, loops=2)
        self.assertEqual((0, 0,), counts)

        [INQ.put_nowait(i) for i in range(9)]
        counts = _qcpy(deck, INQ, OUTQ, arg, loops=1)
        self.assertEqual((9, 9,), counts)
        self.assertEqual(9, OUTQ.qsize())
        emptyout()
        self.assertTrue(OUTQ.empty())

        [INQ.put_nowait(i) for i in range(15)]
        counts = _qcpy(deck, INQ, OUTQ, arg, loops=2)
        self.assertEqual((15, 15,), counts)
        self.assertEqual(15, OUTQ.qsize())
        emptyout()

        deck = Deck(20)
        OUTQ = CTX.JoinableQueue(maxsize=5)
        [INQ.put_nowait(i) for i in range(15)]
        counts = _qcpy(deck, INQ, OUTQ, arg, loops=2)

        self.assertEqual(10, len(deck))
        self.assertEqual((15, 5,), counts)
        self.assertEqual(5, OUTQ.qsize())
        self.assertTrue(INQ.empty())
        emptyout()
        counts = _qcpy(deck, INQ, OUTQ, arg, loops=2)
        self.assertEqual(5, len(deck))
        self.assertEqual((0, 5,), counts)
        self.assertEqual(5, OUTQ.qsize())
        emptyout()
        #######################################
        # here are reaonably sure the sequentual operation  works
        # need to test threaded

    # ******************************************************

    def testB003_basic_thread_operation(self):
        """testB003_basic_thread_operation

        The two seperate operations in this section make sure that
        1) disabled threads start and end correctly
        2) that all the threads can be started and operate reaonable (with test data)
        3) the only data sent on a queue is to the TESTQ which basically the result of myprint calls
           and the debug text output for this is disabled by default.

        these tests check operation of trackermain.timedwork, but not much else as all the test
        functions are in the test routine

        differences between 001 and 003:
        expected timeing has changed in 5

        """
        cleartestq()
        barrier: CTX.Barrier = CTX.Barrier(0)
        timesdic = {'tf': 5, 'nf': 1, 'dqr': 2, 'da': 3, 'db': 4}

        def tf(arg: Threadargs, **kwargs):  # the program periodically executed by the timer thread
            """tf()

            """
            que = arg.qs[QK.dQ]
            data = f'tf th={threading.current_thread().getName()}, t={monotonic()}'
            que.put_nowait(data)

        def nf(arg: Threadargs, **kwargs):
            """
            noisefloor proxy
            arg is named tuple Threadargs
            """
            def doita():  # the program to be run by _thread_template the return 0 says that no work need be done when stopping
                data: str = f'{mma.name} th={threading.current_thread().getName()}, t={monotonic()}'
                q = arg.qs[QK.dQ]
                aa = q.put_nowait(data)
                return 1

            # update the interval and function
            mma = arg._replace(
                interval=timesdic[arg.name], doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def dqr(arg: Threadargs, **kwargs):
            """
            data processing proxie
            arg is named tuple Threadargs
            """
            deck: Deck = Deck(10)

            def doita():
                # (deckin, qin, qout, args, markdone=True, **kwargs) -> Tuple[int, int]:

                aa: Tuple[int, int] = trackermain._qcpy(
                    deck, mma.qs[QK.dQ], mma.qs[QK.dpQ], arg)
                return aa

            # update the interval and function
            deck = Deck(50)
            mma = arg._replace(doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def da(arg: Threadargs, **kwargs):
            """
            Data Aggragator proxie
            arg is named tuple Threadargs
            """
            deck = Deck(50)

            def doita():
                aa: Tuple[int, int] = trackermain._qcpy(
                    deck, mma.qs[QK.dpQ], mma.qs[QK.dbQ], arg)
                return aa

            # update the interval and function
            mma = arg._replace(
                doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def db(arg: Threadargs, **kwargs):
            """
            database proxie
            arg is named tuple Threadargs
            """
            deck = Deck(50)

            def doita():
                aa: Tuple[int, int] = trackermain._qcpy(
                    deck, mma.qs[QK.dbQ], TESTOUTQ, arg)
                return aa

            # update the interval and function
            mma = arg._replace(
                interval=1, doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        # turn on all threads
        bollst: Tuple[bool, ...] = ENABLES(
            w=True, n=True, t=True, da=True, db=True,)
        # bollst = (True, True, True, True, True)
        # count them for barrier the plus 1 is for this thread
        bc = sum([1 for _ in bollst if _]) + 1
        barrier = CTX.Barrier(bc)
        runtime = 30  # get 36 readings per 30 second
        cleartestq()
        RESET_STOP_EVENTS()

        """
        Start the threads, the weather and noise send to dataQ, and the others just pass it along
        The db copies to the TESTQ
        """

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            argdic = genargs(barrier, bollst)

            # mods for test
            argdic[AK.w] = argdic[AK.w]._replace(
                interval=5, doit=tf)
            argdic[AK.n] = argdic[AK.n]._replace(
                interval=4)
            argdic[AK.t] = argdic[AK.t]._replace(
                interval=timesdic['dqr'])
            argdic[AK.da] = argdic[AK.da]._replace(
                interval=timesdic['da'])
            argdic[AK.db] = argdic[AK.db]._replace(
                interval=timesdic['db'])

            futures = {}

            # gets weather data
            futures[FK.w] = tpex.submit(
                trackermain.timed_work, argdic[AK.w], printfn=myprint)

            # gets banddata data
            futures[FK.n] = tpex.submit(nf, argdic[AK.n])

            # reads the dataQ and sends to the data processing queue dpq
            futures[FK.t] = tpex.submit(dqr, argdic[AK.t])

            # looks at the data and generates the approprate sql to send to dbwriter
            futures[FK.da] = tpex.submit(da, argdic[AK.da])

            # reads the database Q and writes it to the database
            futures[FK.db] = tpex.submit(db, argdic[AK.db])

            _ = tpex.submit(breakwait, barrier)
            _.add_done_callback(bwdone)

            # for _ in range(runtime):
            # wait for a while to let the threads work get 36 readings per second
            # Sleep(1)
            Sleep(runtime)

            waitresults: Tuple[Set, Set] = trackermain.shutdown(
                futures, QUEUES, STOP_EVENTS)
            self.assertEqual(5, len(waitresults.done))
            self.assertEqual(0, len(waitresults.not_done))

        queuedd = [  # example data for sleep 30 approx
            'nf th=dbc-_1, t=41787.453',
            'nf th=dbc-_1, t=41788.625',
            'nf th=dbc-_1, t=41789.625',
            'nf th=dbc-_1, t=41790.64',
            'nf th=dbc-_1, t=41791.64',
            'tf th=dbc-_0, t=41792.453',
            'tf th=dbc-_0, t=41792.453',
            'tf th=dbc-_0, t=41792.453',
            'nf th=dbc-_1, t=41792.64',
            'nf th=dbc-_1, t=41793.64',
            'nf th=dbc-_1, t=41794.64',
            'nf th=dbc-_1, t=41795.64',
            'nf th=dbc-_1, t=41796.64',
            'tf th=dbc-_0, t=41797.453',
            'nf th=dbc-_1, t=41797.64',
            'nf th=dbc-_1, t=41798.64',
            'nf th=dbc-_1, t=41799.64',
            'nf th=dbc-_1, t=41800.64',
            'nf th=dbc-_1, t=41801.64',
            'tf th=dbc-_0, t=41802.453',
            'nf th=dbc-_1, t=41802.64',
            'nf th=dbc-_1, t=41803.64',
            'nf th=dbc-_1, t=41804.64',
            'nf th=dbc-_1, t=41805.64',
            'nf th=dbc-_1, t=41806.64',
            'tf th=dbc-_0, t=41807.453',
            'nf th=dbc-_1, t=41807.64',
            'nf th=dbc-_1, t=41808.64',
            'nf th=dbc-_1, t=41809.656',
            'nf th=dbc-_1, t=41810.656',
            'nf th=dbc-_1, t=41811.656',
            'tf th=dbc-_0, t=41812.453',
            'nf th=dbc-_1, t=41812.656',
            'nf th=dbc-_1, t=41813.656',
            'nf th=dbc-_1, t=41814.656',
            'nf th=dbc-_1, t=41815.656',
            'nf th=dbc-_1, t=41816.656',
            'tf th=dbc-_0, t=41817.453',
        ]
        tfn = [f for f in queuedd if 'tf ' in f]
        nfn = [f for f in queuedd if 'nf ' in f]
        self.assertEqual(8, len(tfn))
        self.assertEqual(30, len(nfn))

        for k, v in QUEUES.items():
            self.assertEqual(0, v.qsize())

        testqdec = Deck(500)
        testqdec.q2deck(TESTOUTQ, True)
        testlist = []
        try:
            while True:
                testlist.append(testqdec.popleft())
        except:
            pass

        tfn = [f for f in testlist if 'tf ' in f]
        nfn = [f for f in testlist if 'nf ' in f]
        self.assertTrue(4 <= len(tfn) <= 7)
        self.assertEqual(30, len(nfn))

        testqdeck = Deck(200)
        testqdeck.q2deck(TESTQ, True)
        testlist = []
        try:
            while True:
                testlist.append(testqdeck.popleft())
        except:
            pass

        calldic: Dict[str, List[str]] = {
        }
        # seperate the type of message
        for _ in testlist:
            x = _.split(' ', 1)
            try:
                calldic[x[0]].append(x[1])
            except KeyError:
                calldic[x[0]] = [x[1]]

        self.assertEqual(2, len(calldic['breakwait']))
        for _ in ['timed_work', 'nf', 'dqr', 'da', 'db']:
            self.assertEqual(4, len(calldic[_]))

    def testB001_basic_thread_operation(self):
        """testB001_basic_thread_operation

        The two seperate operations in this section make sure that
        1) shutdown works with no threads, first and 3rd thread and 3rd and 5th threads
        2) disabled threads start and end correctly
        3) that all the threads can be started and operate reaonable (with test data)
        the only data sent on a queue is to the TESTQ which basically the result of myprint calls
           and the debug text output for this is disabled by default.

        these tests check operation of trackermain.timedwork, but not much else as all the test
        functions are in the test routine
        """

        from queuesandevents import CTX, QUEUES, STOP_EVENTS
        cleartestq()
        barrier: CTX.Barrier = CTX.Barrier(0)
        timesdic = {'tf': 15, 'nf': 4, 'dqr': 5, 'da': 6, 'db': 7}

        def tf(arg: Threadargs, **kwargs):  # the program periodically executed by the timer thread
            """tf()
            Justs writes the thread name and time to TESTQ and maybe the consule
            """
            myprint(
                f'tf th={threading.current_thread().getName()}, t={monotonic()}')

        def nf(arg: Threadargs, **kwargs):
            """
            noisefloor proxy
            arg is named tuple Threadargs

            Justs writes the routine name, thread name and time to TESTQ and maybe the consule

            """
            def doita():  # the program to be run by _thread_template the return 0 says that no work need be done when stopping
                myprint(
                    f'{mma.name} th={threading.current_thread().getName()}, t={monotonic()}')
                return 0

            # update the interval and function
            mma: Threadargs = arg._replace(
                interval=timesdic[arg.name], doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def dqr(arg: Threadargs, **kwargs):
            """
            data processing proxie
            arg is named tuple Threadargs
            Justs writes the routine name, thread name and time to TESTQ and maybe the consule
            """
            def doita():
                myprint(
                    f'{mma.name} th={threading.current_thread().getName()}, t={monotonic()}')
                return 0

            # update the interval and function
            mma: Threadargs = arg._replace(
                interval=timesdic[arg.name], doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def da(arg, **kwargs):
            """
            Data Aggragator proxie
            arg is named tuple Threadargs
            Justs writes the routine name, thread name and time to TESTQ and maybe the consule
            """
            def doita():
                myprint(
                    f'{arg.name} th={threading.current_thread().getName()}, t={monotonic()}')
                return 0

            # update the interval and function
            mma: Threadargs = arg._replace(
                interval=timesdic[arg.name], doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def db(arg, **kwargs):
            """
            database proxie
            arg is named tuple Threadargs
            Justs writes the routine name, thread name and time to TESTQ and maybe the consule
            """
            def doita():
                myprint(
                    f'{arg.name} th={threading.current_thread().getName()}, t={monotonic()}')
                return 0

            # update the interval and function
            mma: Threadargs = arg._replace(
                interval=timesdic[arg.name], doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def runthreads(argdicin: Dict[str, Threadargs]) -> Dict[str, Any]:
            futures: Dict[str, Any] = {}
            futures[FK.w] = tpex.submit(
                trackermain.timed_work, argdicin[AK.w], printfn=myprint)

            # gets banddata data
            futures[FK.n] = tpex.submit(nf, argdicin[AK.n])

            # reads the dataQ and sends to the data processing queue dpq
            futures[FK.t] = tpex.submit(dqr, argdicin[AK.t])

            # looks at the data and generates the approprate sql to send to dbwriter
            futures[FK.da] = tpex.submit(da, argdicin[AK.da])

            # reads the database Q and writes it to the database
            futures[FK.db] = tpex.submit(db, argdicin[AK.db])

            _ = tpex.submit(breakwait, barrier)
            _.add_done_callback(bwdone)
            return futures

        # turn off all selected threads so they just start and execute
        #bollst: Tuple[bool] = (False, False, False, False, False,)
        bollst: Tuple[bool, ...] = ENABLES(
            w=False, n=False, t=False, da=False, db=False,)
        bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier
        barrier: CTX.Barrier = CTX.Barrier(bc)
        futures_empty: Dict[str, Any] = {}
        self.assertTrue(trackermain.shutdown(
            futures_empty, QUEUES, STOP_EVENTS, time_out=1) is None)

        argdic = genargs(barrier, bollst)

        waitresults: Tuple[Set, Set] = None
        #
        # Check empty submit works with tracker.shutdown
        #
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            # no threads running
            futures: Dict[str, Any] = {}
            for _ in range(5):
                Sleep(1)  # wait for a while to let the threads work

            waitresults: Tuple[Set, Set] = trackermain.shutdown(
                futures, QUEUES, STOP_EVENTS)
            self.assertTrue(waitresults is None)
        #
        # Check submit works with all threads disabled
        #
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            futures: Dict[str, Any] = runthreads(argdic)
            for _ in range(1):
                Sleep(1)  # wait for a while to let the threads work
            waitresults = trackermain.shutdown(
                futures, QUEUES, STOP_EVENTS)  # , timeout=5)

        # all 5 threads ran to completion
        self.assertEqual(5, len(waitresults.done))
        self.assertEqual(0, len(waitresults.not_done))

        cleartestq()
        #bollst: Tuple[bool] = (False, False, False, False, False)
        bollst: Tuple[bool, ...] = ENABLES(
            w=False, n=False, t=False, da=False, db=False,)
        bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier
        barrier: CTX.Barrier = CTX.Barrier(bc)
        myprint('starting')

        argdic = genargs(barrier, bollst)
        # mods for test
        argdic[AK.w] = argdic[AK.w]._replace(
            name='timed_work', interval=10.5, doit=tf)

        """
        Start the threads, all should just activate and then exit leaving a trace thistime
        """
        mythreadname = threading.currentThread().getName()
        mythread = threading.currentThread()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            futures: Dict[str, Any] = runthreads(argdic)
            waitresults = trackermain.shutdown(futures, QUEUES, STOP_EVENTS)

        self.assertEqual(5, len(waitresults.done))
        self.assertEqual(0, len(waitresults.not_done))
        # check that the results were expected
        for _ in waitresults.done:
            self.assertTrue(_.done())
            rrr = repr(_.result())
            self.assertTrue(rrr in ['[]', 'None', 'deque([], maxlen=10)'])

        quedstuff = []  # copy the TESTQ to a list
        try:
            while True:
                d = TESTQ.get(True, .5)
                TESTQ.task_done()
                quedstuff.append(d)
        except QEmpty:
            pass

        expected: List[str] = [
            'starting',
            'timed_work invoked',
            'timed_work disabled',
            'timed_work end',
            'nf invoked,',
            'dqr invoked,',
            'da invoked, ',
            'db invoked,',
            'dqr execution disabled',
            'dqr end',
            'da execution disabled',
            'da end',
            'db execution disabled',
            'db end',
            'nf execution disabled',
            'nf end',
        ]
        # verify that the operation completed sucessfully
        thejoin: str = '\n'.join(quedstuff)
        for _ in expected:
            if _ not in thejoin:
                print(_)
            self.assertTrue(_ in thejoin)

        # print(
            # '\nend of subtest 1 ---------------------------------------------------2\n')

        # turn on all threads
        #bollst = (True, True, True, True, True)
        bollst: Tuple[bool, ...] = ENABLES(
            w=True, n=True, t=True, da=True, db=True,)
        # count them for barrier the plus 1 is for this thread
        bc = sum([1 for _ in bollst if _]) + 1
        barrier = CTX.Barrier(bc)
        runtime = 60  # either 60, or 120 if not one of these, some of the asserts are ignored
        cleartestq()
        RESET_STOP_EVENTS()

        argdic = genargs(barrier, bollst)
        # mods for test
        argdic[AK.w] = argdic[AK.w]._replace(
            interval=timesdic['tf'], doit=tf)
        argdic[AK.n] = argdic[AK.n]._replace(
            interval=timesdic['nf'])
        argdic[AK.t] = argdic[AK.t]._replace(
            interval=timesdic['dqr'])
        argdic[AK.da] = argdic[AK.da]._replace(
            interval=timesdic['da'])
        argdic[AK.db] = argdic[AK.db]._replace(
            interval=timesdic['db'])

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            futures: Dict[str, Any] = runthreads(argdic)
            Sleep(runtime)  # wait for a while to let the threads work
            waitresults = trackermain.shutdown(
                futures, QUEUES, STOP_EVENTS, time_out=60)  # wait max 60 for the threads to stop

        quedstuff = []  # extract the myprint messages from TESTQ
        try:
            while True:
                d = TESTQ.get(True, .5)
                TESTQ.task_done()
                quedstuff.append(d)
        except QEmpty:
            pass

        calldic: Dict[str, List[str]] = {
        }
        # seperate the type of message
        for _ in quedstuff:
            x = _.split(' ', 1)
            try:
                calldic[x[0]].append(x[1])
            except KeyError:
                calldic[x[0]] = [x[1]]

        # print(len(calldic['tf']))
        # print(len(calldic['da']))
        # print(len(calldic['db']))
        # print(len(calldic['dqr']))
        # print(len(calldic['nf']))

        # for k, v in calldic.items():
            #print(f'{k}: {len(v)}')

        # verify expected results
        self.assertEqual(4, len(calldic['timed_work']))
        self.assertEqual(2, len(calldic['breakwait']))
        if runtime == 120:
            self.assertTrue(6 <= len(calldic['tf']) <= 9)
            self.assertTrue(24 <= len(calldic['da']) <= 27)
            self.assertTrue(23 <= len(calldic['db']) <= 25)
            self.assertTrue(28 <= len(calldic['dqr']) <= 30)
            self.assertTrue(34 <= len(calldic['nf']) <= 36)

        elif runtime == 60:
            self.assertTrue(3 <= len(calldic['tf']) <= 5)
            self.assertTrue(14 <= len(calldic['da']) <= 17)
            self.assertTrue(13 <= len(calldic['db']) <= 17)
            self.assertTrue(16 <= len(calldic['dqr']) <= 18)
            self.assertTrue(18 <= len(calldic['nf']) <= 21)
        else:
            pass

        timeddic: Dict[str, float] = _gentimedict(calldic)
        _trimstartend(timeddic, ['da', 'db', 'dqr', 'nf'])
        avgtdict: Dict[str, float] = _avragedict(timeddic)
        print(avgtdict)
        if not _checktiming(timesdic, avgtdict):
            print('POSSIBLE TIMEING ERROR')
        seqlist: List(Tuple[str, float]) = []

        history: Dict[float, str] = {}  # not analizing this
        for k, v in calldic.items():
            for aa in v:
                if 't=' in aa:
                    _w = aa.split('t=', 1)
                    _wf = float(_w[1])
                    try:
                        history[_wf].append(f'{k}: {aa}')
                    except KeyError:
                        history[_wf] = []
                        history[_wf].append(f'{k}: {aa}')

        keys = history.keys()
        keysl = list(keys)
        keysl.sort()
        first = keysl[0]
        last = keysl[-1]
        timetocomplete: float = last - first
        self.assertTrue(timetocomplete < runtime + 31.5)

        historyredux: Dict(str, List[str]) = {}
        for k, v in history.items():
            sk = str(round(k, 1))
            try:
                historyredux[sk].append(f'{k}: {v}')
            except KeyError:
                historyredux[sk] = []
                historyredux[sk].append(f'{k}: {v}')

        print('do something with this data')

        # print(
        # '\nend of subtest 1 ---------------------------------------------------3\n')
        cleartestq()
        clearstopevents()

        # generate total time sequence

# -------------------------------------

    def testB008_basic_thread_operation(self):
        """
        testB007_basic_thread_operation
        Similar to testB005, but testing data gen in trackermain
        """

        barrier: CTX.Barrier = None
        futures: Dict[str, Any] = {}

        cleartestq()
        RESET_STOP_EVENTS()
        # turn on all threads
        bollst: Tuple[bool, ...] = ENABLES(
            w=True, n=True, t=True, da=True, db=True,)
        #bollst: Tuple[bool] = (True, True, False, False, False)
        # count them for barrier the plus 1 is for this thread
        bc: int = sum([1 for _ in bollst if _]) + 1
        barrier = CTX.Barrier(bc)
        runtime = 1200 #20 min
        shutdown_result: Tuple[Set, Set] = None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            argdic = genargs(barrier, bollst)

            # mods for test
            argdic[AK.w] = argdic[AK.w]._replace(
                name='timed_work', interval=120, doit=trackermain.Get_LW)

            #argdic[AK.w] = argdic[AK.w]._replace(
                #name='timed_work', interval=60 * 3.5, doit=Get_LW)


            argdic[AK.n] = argdic[AK.n]._replace(
                interval=90)
            argdic[AK.t] = argdic[AK.t]._replace(
                interval=1)
            argdic[AK.da] = argdic[AK.da]._replace(
                interval=1)
            argdic[AK.db] = argdic[AK.db]._replace(
                interval=1)

            futures = {}

            # gets weather data
            futures[FK.w] = tpex.submit(
                trackermain.timed_work, argdic[AK.w], printfn=myprint)

            # gets banddata data
            futures[FK.n] = tpex.submit(
                trackermain.get_noise1, argdic[AK.n])


            # reads the dataQ and sends to the data processing queue dpq
            futures[FK.t] = tpex.submit(
                trackermain.dataQ_reader_dbg, argdic[AK.t], printfn=myprint)


            # looks at the data and generates the approprate sql to send to dbwriter
            futures[FK.da] = tpex.submit(
                trackermain.dataaggrator_dbg, argdic[AK.da], printfn=myprint)

            # reads the database Q and writes it to the database
            futures[FK.db] = tpex.submit(
                trackermain.dbQ_writer_dbg, argdic[AK.db], debugResultQ=TESTQ)
            Sleep(10)

            _ = tpex.submit(trackermain._breakwait, barrier)

            rt = int(runtime/4)
            for _ in range(rt):
                Sleep(4)

            shutdown_result = trackermain.shutdown(
                futures, QUEUES, STOP_EVENTS)
            self.assertFalse(shutdown_result.not_done)

        deck: Deck = Deck(400)
        deck.q2deck(TESTQ, True)
        decklst = deck.deck2lst()
        sepstup:SepDataTup = trackermain.seperate_data(decklst)
        #print(f'{sepstup}') #sshould expand this out
        self.assertEqual(4,len(sepstup.strr))
        self.assertTrue(6<=len(sepstup.nfq)<=8)
        self.assertTrue(10<=len(sepstup.lwq)<=12)
        #self.assertFalse(sepstup.lwq)
        self.assertFalse(sepstup.other)


# ---------------------------------
    def testA004_genfilename(self):
        aa:str = trackermain._genfilename(0)
        self.assertEqual('0:0', aa)
        aa:str = trackermain._genfilename(.25)
        self.assertEqual('0:15', aa)
        aa:str = trackermain._genfilename(.5)
        self.assertEqual('0:30', aa)
        aa:str = trackermain._genfilename(1.0)
        self.assertEqual('1:0', aa)
        aa:str = trackermain._genfilename(0.1666666)
        self.assertEqual('0:10', aa)
        aa:str = trackermain._genfilename(0.3333333)
        self.assertEqual('0:20', aa)
        aa:str = trackermain._genfilename(1.3333333)
        self.assertEqual('1:20', aa)

        aa:str = trackermain._genfilename(.1)
        self.assertEqual('0:10', aa)
        aa:str = trackermain._genfilename(.24)
        self.assertEqual('0:15', aa)
        aa:str = trackermain._genfilename(.26)
        self.assertEqual('0:15', aa)
        aa:str = trackermain._genfilename(.4)
        self.assertEqual('0:20', aa)
        aa:str = trackermain._genfilename(.6)
        self.assertEqual('0:40', aa)
        aa:str = trackermain._genfilename(1.01)
        self.assertEqual('1:0', aa)
        aa:str = trackermain._genfilename(0.2)
        self.assertEqual('0:10', aa)
        aa:str = trackermain._genfilename(0.34)
        self.assertEqual('0:20', aa)
        aa:str = trackermain._genfilename(1.12445)
        self.assertEqual('1:10', aa)

    def testB007_basic_thread_operation(self):
        """
        testB007_basic_thread_operation
        Similar to testB005, but testing data gen in trackermain
        """

        barrier: CTX.Barrier = None
        futures: Dict[str, Any] = {}

        cleartestq()
        RESET_STOP_EVENTS()
        # turn on all threads

        bollst: Tuple[bool, ...] = ENABLES(
            w=True, n=True, t=True, da=True, db=True,)
        # count them for barrier the plus 1 is for this thread
        bc: int = sum([1 for _ in bollst if _]) + 1
        barrier = CTX.Barrier(bc)
        runtime = 15
        shutdown_result: Tuple[Set, Set] = None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            argdic = genargs(barrier, bollst)

            # mods for test
            argdic[AK.w] = argdic[AK.w]._replace(
                interval=3, doit=trackermain.Get_LW_dbg)
            argdic[AK.n] = argdic[AK.n]._replace(
                interval=2)
            argdic[AK.t] = argdic[AK.t]._replace(
                interval=1)
            argdic[AK.da] = argdic[AK.da]._replace(
                interval=1)
            argdic[AK.db] = argdic[AK.db]._replace(
                interval=1)

            futures = {}

            # gets weather data
            futures[FK.w] = tpex.submit(
                trackermain.timed_work, argdic[AK.w], printfn=myprint)

            # gets banddata data
            futures[FK.n] = tpex.submit(
                trackermain.Get_NF_dbg, argdic[AK.n])

            # reads the dataQ and sends to the data processing queue dpq
            futures[FK.t] = tpex.submit(
                trackermain.dataQ_reader_dbg, argdic[AK.t], printfn=myprint)

            # looks at the data and generates the approprate sql to send to dbwriter
            futures[FK.da] = tpex.submit(
                trackermain.dataaggrator_dbg, argdic[AK.da], printfn=myprint)

            # reads the database Q and writes it to the database
            futures[FK.db] = tpex.submit(
                trackermain.dbQ_writer_dbg, argdic[AK.db], debugResultQ=TESTQ)

            _ = tpex.submit(trackermain._breakwait, barrier)

            Sleep(runtime)
            shutdown_result = trackermain.shutdown(
                futures, QUEUES, STOP_EVENTS)
            self.assertFalse(shutdown_result.not_done)

        deck: Deck = Deck(400)
        deck.q2deck(TESTQ, True)
        _ = deck.deck2lst()
        decklst = [x for x in _ if not x.startswith('timed_work ')]
        self.assertEqual(10, len(decklst))

        jjj: Dict[str, List[Any]] = {}
        for k in decklst:
            kk = k.split(None, 1)
            try:
                jjj[kk[0]].append(kk[1])
            except:
                jjj[kk[0]] = []
                jjj[kk[0]].append(kk[1])

        self.assertEqual(2, len(jjj.keys()))
        nfr = jjj['Get_NF_dbg']
        lwr = jjj['timed_work_Get_LW_dbg']
        def _gettimes(a:str)->float:
            aa = a.split('t=',2)
            return (float(aa[1]))

        nfrt:List[float] = [_gettimes(x) for x in nfr]
        lwrt:List[float]= [_gettimes(x) for x in lwr]
        lwrtPDifs:List[float] = []
        for i in range(1,len(lwrt)):
            lwrtPDifs.append(lwrt[i]-lwrt[i-1])

        nfrtPDifs:List[float] = []
        for i in range(1,len(nfrt)):
            nfrtPDifs.append(nfrt[i]-nfrt[i-1])
        nfrm:float= fmean(nfrtPDifs)
        print(lwrtPDifs[0],nfrm)
        self.assertTrue(2.6<= lwrtPDifs[0]<=3.1)
        self.assertTrue(1.8<=nfrm<=2.1)


    def testB005_basic_thread_operation(self):
        """
        testB005_basic_thread_operation
        Similar to testB003, but testing thread debug functions in trackermain
        """

        barrier: CTX.Barrier = None
        futures: Dict[str, Any] = {}
        # turn on all threads except the radio thread
        #bollst: Tuple[bool] = (False, False, False, False, False)
        bollst: Tuple[bool, ...] = ENABLES(
            w=False, n=False, t=False, da=False, db=False,)
        # count them for barrier the plus 1 is for this thread
        bc: int = sum([1 for _ in bollst if _]) + 1
        barrier = CTX.Barrier(bc)
        runtime = 5  # either 60, or 120 if not one of these, some of the asserts are ignored
        cleartestq()
        RESET_STOP_EVENTS()
        self.assertEqual(0, TESTQ.qsize())

        """

        Start the threads, check to make sure all are inactive
        """

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            argdic = genargs(barrier, bollst)

            # mods for test
            argdic[AK.w] = argdic[AK.w]._replace(
                interval=6, doit=trackermain.Get_LW_dbg)
            argdic[AK.n] = argdic[AK.n]._replace(
                interval=1)
            argdic[AK.t] = argdic[AK.t]._replace(
                interval=1)
            argdic[AK.da] = argdic[AK.da]._replace(
                interval=1)
            argdic[AK.db] = argdic[AK.db]._replace(
                interval=1)

            futures = {}

            # gets weather data
            futures[FK.w] = tpex.submit(
                trackermain.timed_work, argdic[AK.w])

            # gets banddata data
            futures[FK.n] = tpex.submit(
                trackermain.Get_NF_dbg, argdic[AK.n])

            # reads the dataQ and sends to the data processing queue dpq
            futures[FK.t] = tpex.submit(
                trackermain.dataQ_reader_dbg, argdic[AK.t])

            # looks at the data and generates the approprate sql to send to dbwriter
            futures[FK.da] = tpex.submit(
                trackermain.dataaggrator_dbg, argdic[AK.da])

            # reads the database Q and writes it to the database
            futures[FK.db] = tpex.submit(
                trackermain.dbQ_writer_dbg, argdic[AK.db], debugResultQ=TESTQ)

            _ = tpex.submit(trackermain._breakwait, barrier)

            Sleep(1)  # wait for a while to let the threads work
            #

            waitresults: Tuple[Set, Set] = trackermain.shutdown(futures, QUEUES, STOP_EVENTS)
            self.assertEqual(0, TESTQ.qsize())
            for v in futures.values():
                aa = v.done()
                self.assertTrue(v.done())

            self.assertTrue(futures[FK.w].result() is None)
            #for k in ['noise', 'transfer', 'dataagragator', 'dbwriter']:
            for k in [FK.n, FK.t, FK.da, FK.db]:
                self.assertEqual(0, len(futures[k].result()))

        cleartestq()
        RESET_STOP_EVENTS()
        # turn enable t, da, and db threads
        #bollst: Tuple[bool] = (False, False, True, True, True)
        bollst: Tuple[bool, ...] = ENABLES(
            w=False, n=False, t=True, da=True, db=True,)
        # count them for barrier the plus 1 is for the barrier breaker
        bc: int = sum([1 for _ in bollst if _]) + 1
        barrier = CTX.Barrier(bc)
        runtime = 15  #15 seconds, 15 entries in the dataQ

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            argdic = genargs(barrier, bollst)

            # mods for test
            argdic[AK.w] = argdic[AK.w]._replace(
                interval=60, doit=trackermain.Get_LW_dbg)
            argdic[AK.n] = argdic[AK.n]._replace(
                interval=1)
            argdic[AK.t] = argdic[AK.t]._replace(
                interval=1)
            argdic[AK.da] = argdic[AK.da]._replace(
                interval=1)
            argdic[AK.db] = argdic[AK.db]._replace(
                interval=1)

            futures = {}

            # gets weather data disabled
            futures[FK.w] = tpex.submit(
                trackermain.timed_work, argdic[AK.w])

            # gets banddata data disabled
            futures[FK.n] = tpex.submit(
                trackermain.Get_NF_dbg, argdic[AK.n])

            # reads the dataQ and sends to the data processing queue dpq
            futures[FK.t] = tpex.submit(
                trackermain.dataQ_reader_dbg, argdic[AK.t], printfn=myprint)

            # looks at the data and generates the approprate sql to send to dbwriter
            futures[FK.da] = tpex.submit(
                trackermain.dataaggrator_dbg, argdic[AK.da], printfn=myprint)

            # reads the database Q and writes it to the database
            futures[FK.db] = tpex.submit(
                trackermain.dbQ_writer_dbg, argdic[AK.db], debugResultQ=TESTQ)

            _ = tpex.submit(trackermain._breakwait, barrier) # break the barrier

            for _ in range(runtime):
                QUEUES[QK.dQ].put(f'tick: {monotonic()}')
                Sleep(1)
            # 15 seconds have passed, should have 15 ticks on the TESTQ
            waitresults: Tuple[Set, Set] =trackermain.shutdown(futures, QUEUES, STOP_EVENTS)

        deck: Deck = Deck(400)
        deck.q2deck(TESTQ, True)
        self.assertTrue(runtime - 1 <= len(deck) <= runtime + 1)


    #def testx01a_multiproc_simple(self):
        #"""test01a_threaded_simple()

        #test threads started but quick exit as no function is enabled, and that basic queue
        #operations work as expected

        #"""
        #return
        #print('\ntest01a_threaded_simple\n', end="")
        #RESET_STOP_EVENTS()
        #reset_queues()

        #bollst = [False, False, False, False, False]
        #bc = sum([1 for _ in bollst if _]) + 1

        #barrier = ctx.Barrier(bc)

        #while (True):
            #futures = {}
            #with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                #futures = startThreads(
                    #tpex, bollst, barrier, stopevents, queues)
                #time.sleep(0.00001)
                #barrier.wait(timeout=10)
                #time.sleep(0.00001)
                #myprint(
                    #f'test01a_instat continuing at {str(monotonic())}\n', end="")
                ## trackerstarted = time.monotonic()

                #dpQ_OUT = queues['dpQ']
                #dpQ_IN = queues['dpQ']

                ## put 5 items on the out queue
                #[dpQ_OUT.put(_) for _ in range(5)]
                ## wait a second with 4 chances to do a thread switch
                #[time.sleep(0.25) for _ in range(4)]

                #dpqouts = dpQ_OUT.qsize()
                #dpqins = dpQ_IN.qsize()
                #self.assertEqual(5, dpqouts)
                #self.assertEqual(dpqins, dpqouts)

                ## check all threads are done
                #[self.assertTrue(_.done()) for _ in futures.values()]
                #try:
                    #while True:
                        #dpQ_IN.get_nowait()
                        #dpQ_IN.task_done()
                #except QEmpty:
                    #pass
                #dpqouts = dpQ_OUT.qsize()
                #dpqins = dpQ_IN.qsize()
                #self.assertEqual(0, dpqouts)
                #self.assertEqual(dpqins, dpqouts)

                #pass  # exit out of tpex
            #break  # break out of while
        #trackermain.shutdown(futures, queues, stopevents)
        #barrier.reset()
        ##print('test01a_threaded_simple -- end\n', end="")

    #def testx01b_threaded_simple(self):
        #"""test01b_threaded_simple()

        #Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        #using only get_lw as the function. No transfer to another queue

        #"""
        #return
        #myprint('\ntest01b_threaded_simple\n', end="")
        #RESET_STOP_EVENTS()
        #reset_queues()

        ## trackerinitialized = time.monotonic()
        #trackerstarted = None
        #bollst = [True, False, False, False, False]
        #bc = sum([1 for _ in bollst if _]) + 1

        #barrier = ctx.Barrier(bc)
        #while (True):
            #futures = {}
            #with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                #futures = startThreads(
                    #tpex, bollst, barrier, stopevents, queues)
                #barrier.wait(timeout=10)
                #time.sleep(0.00001)
                #print(
                    #f'test01b_instat continuing at {str(time.monotonic())}\n', end="")
                #trackerstarted = time.monotonic()
                #marktime(dly=2.5, cnt=6)
                #stopevents['acquireData'].set()

                #while not futures.get('weather').done():
                    #time.sleep(0.005)

                #res = futures.get('weather').result()
                #elapsedtime = time.monotonic() - trackerstarted
                #self.assertAlmostEqual(15.04, elapsedtime, places=1)
                ## print(elapsedtime)
                #self.assertEqual(3, len(res))
                #q = queues['dataQ']
                #q.put(-1)
                #theq = []
                #while True:
                    #try:
                        #theq.append(q.get(True, 0.10))
                        #q.task_done()
                    #except QEmpty:
                        #break

                #self.assertEqual(
                    #[0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, -1], theq)
            #break
        #trackermain.shutdown(futures, queues, stopevents)
        #barrier.reset()
        #myprint('test01b_threaded_simple -- end\n', end="")

    #def testx01c_threaded_simple(self):
        #"""test01c_threaded_simple()

        #Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        #using get_NF and get_LW as the functions. Starting both dataacquisition threads

        #"""
        #return
        #print('test0001c_threaded_simple\n', end="")
        #clearstopevents()
        #reset_queues()

        ## trackerinitialized = time.monotonic()
        #trackerstarted = None
        #bollst = [True, True, False, False, False]
        #bc = sum([1 for _ in bollst if _]) + 1

        #barrier = ctx.Barrier(bc)
        #while (True):
            #futures = {}
            #with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                #futures = startThreads(
                    #tpex, bollst, barrier, stopevents, queues)
                #barrier.wait(timeout=10)
                #time.sleep(0.00001)
                #print(
                    #f'test01c_instat continuing at {str(time.monotonic())}\n', end="")
                #trackerstarted = time.monotonic()

                #marktime(dly=2.5, cnt=6)

                ## stops both weather and noise
                #stopevents['acquireData'].set()
                #time.sleep(0.0001)

                #while not (futures.get('weather').done() and futures.get('noise').done()):
                    #time.sleep(0.005)

                #resw = futures.get('weather').result()
                #resn = futures.get('noise').result()

                #elapsedtime = time.monotonic() - trackerstarted
                #self.assertAlmostEqual(15.04, elapsedtime, places=1)
                ## print(elapsedtime)

                #q = queues['dataQ']
                #q.put(-1)
                #theq = []
                #for _ in range(5):
                    #while True:
                        #try:
                            #theq.append(q.get(True, 0.10))
                            #q.task_done()
                        #except QEmpty:
                            #break
                    #time.sleep(0.10)

                ## print(theq)
                #self.assertEqual(31, len(theq))
                #self.assertEqual(6, len([x for x in theq if x == 0]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 1 or x == 10]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 2 or x == 20]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 3 or x == 30]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 4 or x == 40]))

                #self.assertEqual(3, len(resw))
                #self.assertEqual(3, len(resn))
            #break
        #trackermain.shutdown(futures, queues, stopevents)
        #barrier.reset()
        #print('test01c_threaded_simple -- end\n', end="")

    #def testx01d_threaded_simple(self):
        #"""test01d_threaded_simple()

        #Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        #using get_NF, get_LW, and transfer as the functions. Starting both dataacquisition threads

        #"""
        #return
        #print('test01d_threaded_simple\n', end="")
        #clearstopevents()
        #reset_queues()

        ## trackerinitialized = time.monotonic()
        #trackerstarted = None
        #bollst = [True, True, True, False, False]
        #bc = sum([1 for _ in bollst if _]) + 1

        #barrier = ctx.Barrier(bc)
        #while (True):
            #futures = {}
            #with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                #futures = startThreads(
                    #tpex, bollst, barrier, stopevents, queues)
                #barrier.wait(timeout=10)
                #time.sleep(0.00001)
                #print(
                    #f'\ntest01d_instat continuing at {str(time.monotonic())}')
                #trackerstarted = time.monotonic()
                #marktime(dly=2.5, cnt=6)

                ## stops both weather and noise
                #stopevents['acquireData'].set()
                #time.sleep(0.0001)

                #while not (futures.get('weather').done() and futures.get('noise').done()):
                    #time.sleep(0.005)

                #q = queues['dataQ']  # add the last entry to the data q
                #q.put(-1)
                #stopevents['trans'].set()
                #time.sleep(0.00001)
                #while not futures.get('transfer').done():
                    #time.sleep(0.005)

                #elapsedtime = time.monotonic() - trackerstarted
                #self.assertAlmostEqual(25.05, elapsedtime, places=0)
                #resw = futures.get('weather').result()
                #resn = futures.get('noise').result()
                #resr = futures.get('transfer').result()
                #self.assertEqual(31, resr)

                ## print(elapsedtime)
                #self.assertEqual(3, len(resw))
                #self.assertEqual(3, len(resn))

                #q = queues['dpQ']
                #theq = []
                #while True:
                    #try:
                        #theq.append(q.get(True, 0.00010))
                        #q.task_done()
                    #except QEmpty:
                        #break

                #self.assertTrue(31 == len(theq) or 36 == len(theq))
                #self.assertEqual(6, len([x for x in theq if x == 0]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 1 or x == 10]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 2 or x == 20]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 3 or x == 30]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 4 or x == 40]))
                #self.assertEqual(
                    #1, len([x for x in theq if x == -1]))

            #break
        #trackermain.shutdown(futures, queues, stopevents)
        #barrier.reset()
        #print('test01d_threaded_simple -- end\n', end="")

    #def testx01e_threaded_simple(self):
        #"""test01e_threaded_simple()

        #Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        #using get_NF, get_LW, transfer, and dataagragator as the functions. Starting both dataacquisition threads


        #"""
        #return
        #print('test01e_threaded_simple\n', end='')
        #clearstopevents()
        #reset_queues()

        #trackerstarted = None
        #bollst = [True, True, True, True, False]
        #bc = sum([1 for _ in bollst if _]) + 1

        #barrier = CTX.Barrier(bc)
        #while (True):
            #futures = {}
            #with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                #futures = startThreads(
                    #tpex, bollst, barrier, stopevents, queues)
                #barrier.wait(timeout=100)
                #time.sleep(0.00001)
                #print(
                    #f'test01e_instat continuing at {str(time.monotonic())}\n', end='')
                #trackerstarted = time.monotonic()
                #marktime(dly=2.5, cnt=6)

                ## stops both weather and noise
                #stopevents['acquireData'].set()
                #for _ in range(10):
                    #time.sleep(0.005)

                #while not (futures.get('weather').done() and futures.get('noise').done()):
                    #time.sleep(0.005)

                #stopevents['trans'].set()
                #time.sleep(0.00001)
                #while not futures.get('transfer').done():
                    #time.sleep(0.005)

                ## add the last entry to the data processing q
                #q = queues['dpQ']
                #q.put(-1)
                #for _ in range(6):
                    #time.sleep(0.00001)
                #stopevents['agra'].set()
                #time.sleep(0.00001)

                #while not futures.get('dataagragator').done():
                    #time.sleep(0.005)

                #elapsedtime = time.monotonic() - trackerstarted
                ## okt = 20.0 < elapsedtime < 25.0
                ## self.assertTrue(okt)
                #resw = futures.get('weather').result()
                #resn = futures.get('noise').result()
                #resr = futures.get('transfer').result()
                #resa = futures.get('dataagragator').result()
                ## TODO has a timedependency in this test it sometimes fails
                #self.assertEqual(30, resr)

                ## print(elapsedtime)
                #self.assertEqual(3, len(resw))
                ## self.assertEqual(4, len(resn))

                #q = queues['dbQ']

                #theq = []
                #while True:
                    #try:
                        #theq.append(q.get(True, 0.00010))
                        #q.task_done()
                    #except QEmpty:
                        #break

                #self.assertEqual(31, len(theq))
                #self.assertEqual(6, len([x for x in theq if x == 0]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 10 or x == 100]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 20 or x == 200]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 30 or x == 300]))
                #self.assertEqual(
                    #6, len([x for x in theq if x == 40 or x == 400]))
                #self.assertEqual(
                    #1, len([x for x in theq if x == -10]))

            #break
        #trackermain.shutdown(futures, queues, stopevents)
        #barrier.reset()
        #print('test01e_threaded_simple -- end\n', end='')

    def testA005_queue_overflow(self):
        """testA005_queue_overflow()

        tests that the output queue overflow technique works

        QUEUES in trackermain have default size of 100

        """

        from trackermain import CTX

        clearstopevents()
        reset_queues()

        def tf(arg: Threadargs):  # the program periodically executed by the timer thread
            """tf()

            """
            que = arg.qs[QK.dQ]
            data = f'tf th={threading.current_thread().getName()}, t={monotonic()}'
            que.put_nowait(data)

        def nf(arg: Threadargs, **kwargs):
            """
            noisefloor proxy
            arg is named tuple Threadargs
            """
            def doita():  # the program to be run by _thread_template the return 0 says that no work need be done when stopping
                data = f'{mma.name} th={threading.current_thread().getName()}, t={monotonic()}'
                q = arg.qs[QK.dQ]
                aa = q.put_nowait(data)
                a = 0
                return 1

            # update the interval and function
            mma = arg._replace(
                interval=1, doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def dqr(arg: Threadargs, **kwargs):
            """
            data processing proxie
            arg is named tuple Threadargs
            """
            deck: Deck = Deck(101)

            def doita():
                # (deckin, qin, qout, args, markdone=True, **kwargs) -> Tuple[int, int]:

                aa = trackermain._qcpy(
                    deck, mma.qs[QK.dQ], mma.qs[QK.dpQ], arg)
                return aa

            # update the interval and function

            mma = arg._replace(
                interval=1, doit=doita)
            return _thread_template(
                mma, printfun=myprint, **kwargs)  # run it

        def da(arg, **kwargs):
            """
            Data Aggragator proxie
            arg is named tuple Threadargs
            """
            deck: Deck = Deck(30)

            def doita():
                aa = trackermain._qcpy(
                    deck, mma.qs[QK.dpQ], mma.qs[QK.dbQ], arg)
                return aa

            # update the interval and function
            mma = arg._replace(doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def db(arg, **kwargs):
            """
            database proxie
            arg is named tuple Threadargs
            """
            deck: Deck = Deck(55)

            def doita():
                aa = trackermain._qcpy(deck, mma.qs[QK.dbQ], TESTOUTQ, arg)
                return aa

            # update the interval and function
            mma = arg._replace(doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        # select only transfer to run
        #bollst = [False, False, True, True, True]
        bollst: Tuple[bool, ...] = ENABLES(
            w=False, n=False, t=True, da=True, db=True,)
        bc = sum([1 for _ in bollst if _]) + 1
        # set barrier to 2 threads this one and transfer (by count not by name)
        barrier = CTX.Barrier(bc)

        cleartestq()
        RESET_STOP_EVENTS()
        QUEUES[QK.dQ] = CTX.JoinableQueue(
            maxsize=200)  # dataQ now has max size of 200
        QUEUES[QK.dpQ] = CTX.JoinableQueue(
            maxsize=101)  # dataQ now has max size of 200
        QUEUES[QK.dbQ] = CTX.JoinableQueue(
            maxsize=45)  # dataQ now has max size of 50

        try:
            for _ in range(200):
                QUEUES[QK.dQ].put(_)  # prefill the dataQ queue
        except Exception as _:
            pass

        self.assertEqual(200, QUEUES[QK.dQ].qsize())

        dpQ = QUEUES[QK.dpQ]
        self.assertTrue(dpQ.empty())
        readings = []
        numreadings = 0

        """
        Start the threads, all in dataQ will end up in TESTOUTQ
        """
        # def nfdone(fu):
        #a = 0
        # pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            argdic = genargs(barrier, bollst)

            # mods for test
            # argdic['twargs'] = argdic['twargs']._replace(
            # execute=False)
            # argdic['nfargs'] = argdic['nfargs']._replace(
            # execute=False)
            argdic[AK.t] = argdic[AK.t]._replace(
                interval=1)
            argdic[AK.da] = argdic[AK.da]._replace(
                interval=1)
            argdic[AK.db] = argdic[AK.db]._replace(
                interval=1)

            futures = {}

            # gets weather data
            futures[FK.w] = tpex.submit(
                trackermain.timed_work, argdic[AK.w], printfn=myprint)

            # gets banddata data
            futures[FK.n] = tpex.submit(nf, argdic[AK.n])

            # reads the dataQ and sends to the data processing queue dpq
            futures[FK.t] = tpex.submit(dqr, argdic[AK.t])

            # looks at the data and generates the approprate sql to send to dbwriter
            futures[FK.da] = tpex.submit(da, argdic[AK.da])

            # reads the database Q and writes it to the database
            futures[FK.db] = tpex.submit(db, argdic[AK.db])
            for _ in range(10):
                Sleep(1)

            self.assertTrue(futures[FK.w].done())
            self.assertTrue(futures[FK.n].done())
            self.assertFalse(futures[FK.t].done())
            self.assertFalse(futures[FK.da].done())
            self.assertFalse(futures[FK.db].done())

            _ = tpex.submit(breakwait, barrier)
            _.add_done_callback(bwdone)

            while TESTOUTQ.qsize() < 200:
                Sleep(1)

            waitresults: Tuple[Set, Set] = trackermain.shutdown(
                futures, QUEUES, STOP_EVENTS)
            a = 0

        resultdec: Deck = Deck(300)

        def jj(a):
            ab: str = 'no conversion'
            try:
                ab = str(a)
            except:
                pass

            return ab
        # mark the items done, convert each to text
        aa = resultdec.q2deck(TESTOUTQ, mark_done=True, fn=jj)
        self.assertTrue(200, aa)
        for i in range(200):
            d = resultdec.popleft()
            self.assertTrue(d, str(i))

        # check if all elemenmts from dataQ have been received.
        numreadings = futures['transfer'].result()
        self.assertEqual((200, 200,), numreadings[0])
        self.assertFalse(futures['transfer'].cancelled())
        self.assertFalse(futures['transfer'].exception())
        self.assertEqual((200, 200,), futures['dataagragator'].result()[0])
        self.assertEqual((200, 200,), futures['dbwriter'].result()[0])
        #print('test02_queue_overflow -- end\n', end='')

    def testA003_seperate_data(self):
        decklst=[]
        with open('mixedlst.pickle', 'rb') as fl:
            try:
                decklst=  pickle.load(fl)
            except Exception as ex:
                a = 0

        sepstup:SepDataTup = trackermain.seperate_data(decklst)
        textlst=sepstup.strr
        self.assertEqual(4,len(textlst))
        nfqlst=sepstup.nfq
        self.assertEqual(7,len(nfqlst))
        lwqlst=sepstup.lwq
        self.assertEqual(11,len(lwqlst))
        self.assertFalse(sepstup.other)

    def testA002_trimdups(self):
        from localweather import LocalWeather, MyTime
        import pickle

        deck = deque([])
        results = trackermain.trim_dups(deck, lambda a, b: True)
        self.assertFalse(results)
        deck.extend([1, 2, 3])
        results = trackermain.trim_dups(deck, lambda a, b: True)
        self.assertEqual([(True, 1, 2), (True, 2, 3)], results)
        results = trackermain.trim_dups(deck, lambda a, b: a == b)
        self.assertEqual([(False, 1, 2), (False, 2, 3)], results)
        deck.extend([3, 3, 4, 4, 5, 6, 6, 6])
        results = trackermain.trim_dups(deck, lambda a, b: a == b)
        expected = [(False, 1, 2), (False, 2, 3), (True, 3, 3), (True, 3, 3),
                    (False, 3, 4), (True, 4, 4), (False, 4, 5), (False, 5, 6),
                    (True, 6, 6), (True, 6, 6)]
        self.assertEqual(expected, results)

        def testfun(a, b):
            return a == b
        results = trackermain.trim_dups(deck, testfun)
        expected = [(False, 1, 2), (False, 2, 3), (True, 3, 3), (True, 3, 3),
                    (False, 3, 4), (True, 4, 4), (False, 4, 5), (False, 5, 6),
                    (True, 6, 6), (True, 6, 6)]

        class Jjj:
            def __init__(self, val):
                self.v = val

            def __str__(self):
                return str(self.v)

        deck = deque([Jjj(1), Jjj(2), Jjj(3), Jjj(4), Jjj(4),
                      Jjj(5), Jjj(6), Jjj(6), Jjj(7), Jjj(8)])

        def testfun(a, b):
            return a.v == b.v
        results = trackermain.trim_dups(deck, testfun)
        self.assertEqual([False, False, False, True, False,
                          False, True, False, False], [j[0] for j in results])
        self.assertEqual([1, 2, 3, 4, 4, 5, 6, 6, 7],
                         [j[1].v for j in results])
        self.assertEqual([2, 3, 4, 4, 5, 6, 6, 7, 8],
                         [j[2].v for j in results])
        a = 0
        local_weather_lst = []
        with open('testlocalWeather62.pickle', 'rb') as fl1:
            try:
                local_weather_lst = pickle.load(fl1)
                a = 0
            except Exception as ex:
                a = 0
        deck = deque(local_weather_lst)
        _lw1 = local_weather_lst[0]

        def equaltemps(a: LocalWeather, b: LocalWeather):
            return a.maint['temp'][0] == b.maint['temp'][0]

        trimlst = trackermain.trim_dups(deck, equaltemps)
        trimlstf = [(a[1], a[2],) for a in trimlst if not a[0]]
        trimlstt = [(a[1], a[2],) for a in trimlst if a[0]]
        self.assertEqual(3, len(trimlstf))
        self.assertEqual(6, len(trimlstt))


if __name__ == '__main__':

    freeze_support()
    unittest.main()
