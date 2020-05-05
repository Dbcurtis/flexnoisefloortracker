#!/usr/bin/env python3.7
"""
Test file for need
"""

# import datetime
from typing import Any, List, Dict, Tuple
from multiprocessing import freeze_support
import unittest
import multiprocessing as mp
from queue import Empty as QEmpty, Full as QFull
# from multiprocessing import queues as QS]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
import concurrent
import time
from collections import deque
from time import sleep as Sleep
from time import monotonic
from concurrent.futures import ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED
import threading
import statistics


import context
from deck import Deck
import trackermain
from queuesandevents import QUEUES as queues
from queuesandevents import RESET_QS as reset_queues
from queuesandevents import CTX as ctx
from queuesandevents import STOP_EVENTS as stopevents


def marktime(dly=2.5, cnt=6):
    for _ in range(cnt):
        print('|', end='')
        time.sleep(dly)
    print('', end=None)


def clearstopevents():
    [e.clear() for e in stopevents.values()]
    # for e in stopevents.values():
    # e.clear()


def startThreads(tpex, bollst, barrier, stopevents, queues):
    """startThreads(tpex, bollst, barrier, stopevents, queues)

     starts the weather, noise, transfer, dataagragator, and dbwriter threads responsive to the bollst boolena array

     tpex is the executor
     bollst is the boolean list specifying which threads to start
     barrier is the barrier to wait on for all the selected threads to start on
     stopevents is the dict of stop events specifying which event the thread is to stop resonive to.
     queues is the dict of queues.
    """

    threadinfo = {
        'weather': (bollst[0], barrier, stopevents['acquireData'], queues,),
        'noise': (bollst[1], barrier, stopevents['acquireData'], queues,),
        'transfer': (bollst[2], barrier, stopevents['trans'], queues,),
        'dataagragator': (bollst[3], barrier, stopevents['agra'], queues,),
        'dbwriter': (bollst[4], barrier, stopevents['dbwrite'], queues,),
    }

    futures = {
        # gets weather data
        'weather': tpex.submit(trackermain.timed_work, threadinfo['weather'], 5, Get_LW),
        # gets banddata data
        'noise': tpex.submit(trackermain.timed_work, threadinfo['noise'], 5, Get_NF),
        # reads the dataQ and sends to the data processing queue dpq
        'transfer': tpex.submit(trackermain.dataQ_reader, threadinfo['transfer']),
        # looks at the data and generates the approprate sql to send to dbwriter
        'dataagragator': tpex.submit(trackermain.dataaggrator, threadinfo['dataagragator'], debugfn=aggrfn),
        # reads the database Q and writes it to the database
        'dbwriter': tpex.submit(trackermain.dbQ_writer, threadinfo['dbwriter'], debugfn=dbconsum)

    }
    return futures


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

        deck.load_from_Q(dpQ_IN, False, 5)
        time.sleep(0.001)  # provide oppertunity to switch threads

        notstop = not stop_event.is_set()
        while notstop or len(deck) > 0:
            if len(deck) == 0:
                break
            deck.loadQ(dbQ_OUT, dpQ_IN, lambda a: a * 10)
            if stop_event.is_set() and dpQ_IN.empty():
                break

        doit = not stop_event.wait(6)

    for _ in range(10):  # get any late queued info
        deck.load_from_Q(dpQ_IN, False, 0.5)
        while True:
            try:  # empty deck to dbQ_OUT
                deck.loadQ(dbQ_OUT, dpQ_IN, lambda a: a * 10)
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
        pass

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

    def test0_multithread_disabled(self):
        from queuesandevents import CTX, QUEUES, STOP_EVENTS
        # Testing queue to gather info
        testq = CTX.JoinableQueue(maxsize=500)
        queues = QUEUES
        # timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)

        # turn on selected threads
        bollst: Tuple[bool] = (False, False, False, False, False)
        bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier

        barrier: CTX.Barrier = CTX.Barrier(bc)

        timesdic = {'tf': 15, 'nf': 4, 'dqr': 5, 'da': 6, 'db': 7}

        def myprint(st):
            print(st)
            testq.put(st)

        def tf(*args):
            """tf()

            """
            myprint(
                f'tf th={threading.current_thread().getName()}, t={monotonic()}')

        """
                myprint(
                    f'{name} invoked, t={threading.current_thread().getName()}')
                Sleep(1.5)
                if args[0]:
                    myprint(f'{name}  execution enabled waiting')
                    args[1].wait()
                    myprint(f'{name} starting')
                else:
                    myprint(f'{name} execution disabled')
                myprint(f'{name}  end')

        """

        def _funtem(args: List[Any]):
            """_funtem(*args)
            *args is (execute, barrier, stop_event, queues,name,interval,doit)

            """
            locald = threading.local()
            locald.name = args[4]
            locald.interval = args[5]
            locald.doit = args[6]
            myprint(
                f'{locald.name} invoked, th={threading.current_thread().getName()}, t={monotonic()}')

            if args[0]:
                myprint(f'{locald.name} execution enabled waiting')
                args[1].wait()
                myprint(
                    f'{locald.name} starting, th={threading.current_thread().getName()}, t={monotonic()}')
                while not args[2].wait(locald.interval):
                    locald.doit()

            else:
                myprint(f'{locald.name} execution disabled')

            myprint(
                f'{locald.name} end, th={threading.current_thread().getName()}, t={monotonic()}')

        def nf(*args):
            """

            *args is (execute, barrier, stop_event, queues,)
            """
            name = 'nf'
            myargs = list(args)
            myargs.append(name)
            myargs.append(timesdic[name])

            def doit():
                myprint(
                    f'{name} th={threading.current_thread().getName()}, t={monotonic()}')
            myargs.append(doit)
            # tup = tuple(myargs)
            _funtem(myargs)

        def dqr(*args):
            """

            *args is (execute, barrier, stop_event, queues,)
            """
            name = 'dqr'
            myargs = list(args)
            myargs.append(name)
            myargs.append(timesdic[name])

            def doit():
                myprint(
                    f'{name} th={threading.current_thread().getName()}, t={monotonic()}')
            myargs.append(doit)
            _funtem(myargs)

        def da(*args):
            """

            *args is (execute, barrier, stop_event, queues,)
            """
            name = 'da'
            myargs = list(args)
            myargs.append(name)
            myargs.append(timesdic[name])

            def doit():
                myprint(
                    f'{name} th={threading.current_thread().getName()}, t={monotonic()}')
            myargs.append(doit)
            _funtem(myargs)

        def db(*args):
            """

            *args is (execute, barrier, stop_event, queues,)
            """

            name = 'db'
            myargs = list(args)
            myargs.append(name)
            myargs.append(timesdic[name])

            def doit():
                myprint(
                    f'{name} th={threading.current_thread().getName()}, t={monotonic()}')
            myargs.append(doit)
            _funtem(myargs)

        futures: Dict[str, Any] = {}
        myprint('starting')

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            futures = {
                # gets weather data
                'weather': tpex.submit(trackermain.timed_work, bollst[0], barrier, STOP_EVENTS['acquireData'], queues, delay=10.5, timed_func=tf),
                # gets banddata data
                # #'noise': tpex.submit(timed_work, bollst[1], barrier, STOP_EVENTS['acquireData'], 60, Get_NF, queues),
                'noise': tpex.submit(nf, bollst[1], barrier, STOP_EVENTS['acquireData'], queues),
                # reads the dataQ and sends to the data processing queue dpq
                'transfer': tpex.submit(dqr, bollst[2], barrier, STOP_EVENTS['trans'], queues),
                # looks at the data and generates the approprate sql to send to dbwriter
                'dataagragator': tpex.submit(da, bollst[3], barrier, STOP_EVENTS['agra'], queues),
                # reads the database Q and writes it to the database
                'dbwriter': tpex.submit(db, bollst[4], barrier, STOP_EVENTS['dbwrite'], queues),

            }

            barrier.wait()  # start them all working

            # as all the threads are disabled, and will end without need of shutdown,
            #  we will wait for them all to complete
            waitresults: Tuple[Set, Set] = concurrent.futures.wait(
                futures.values(), timeout=20, return_when=ALL_COMPLETED)

            _done = waitresults[0]
            self.assertEqual(5, len(_done))
            for _ in _done:
                self.assertTrue(_.done())
                self.assertEqual(None, _.result())

            # shutdown(futures, queues, STOP_EVENTS)

        quedstuff = []
        try:
            while True:
                d = testq.get(True, .5)
                testq.task_done()
                quedstuff.append(d)
        except QEmpty:
            pass

        expected: List[str] = [
            'starting',
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
        thejoin: str = '\n'.join(quedstuff)
        for _ in expected:
            if _ not in thejoin:
                print(_)
            self.assertTrue(_ in thejoin)
        print('end of subtest 1 ---------------------------------------------------')
        # turn on selected threads
        bollst = (True, True, True, True, True)
        bc = sum([1 for _ in bollst if _]) + 1  # count them for barrier

        runtime = 61  # either 60, or 120 if not one, some of the asserts are ignored

        barrier = CTX.Barrier(bc)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            futures['weather'] = tpex.submit(
                trackermain.timed_work, bollst[0], barrier, STOP_EVENTS['acquireData'], queues, delay=timesdic['tf'], timed_func=tf)
            futures['noise'] = tpex.submit(
                nf, bollst[1], barrier, STOP_EVENTS['acquireData'], queues)
            # reads the dataQ and sends to the data processing queue dpq
            futures['transfer'] = tpex.submit(
                dqr, bollst[2], barrier, STOP_EVENTS['trans'], queues)
            # looks at the data and generates the approprate sql to send to dbwriter
            futures['dataagragator'] = tpex.submit(
                da, bollst[3], barrier, STOP_EVENTS['agra'], queues)
            # reads the database Q and writes it to the database
            futures['dbwriter'] = tpex.submit(
                db, bollst[4], barrier, STOP_EVENTS['dbwrite'], queues)

            a = 0
            barrier.wait()  # start them all working
            Sleep(runtime)
            trackermain.shutdown(futures, queues, STOP_EVENTS)

        quedstuff = []
        try:
            while True:
                d = testq.get(True, .5)
                testq.task_done()
                quedstuff.append(d)
        except QEmpty:
            pass

        calldic: Dict(str, List[str]) = {
            'nf': [],
            'dqr': [],
            'da': [],
            'db': [],
            'tf': [],
        }
        for _ in quedstuff:
            x = _.split(' ', 1)
            calldic[x[0]].append(x[1])

        print(len(calldic['tf']))
        print(len(calldic['da']))
        print(len(calldic['db']))
        print(len(calldic['dqr']))
        print(len(calldic['nf']))

        if runtime == 120:

            self.assertTrue(7 <= len(calldic['tf']) <= 9)
            self.assertTrue(23 <= len(calldic['da']) <= 25)
            self.assertTrue(20 <= len(calldic['db']) <= 22)
            self.assertTrue(26 <= len(calldic['dqr']) <= 28)
            self.assertTrue(32 <= len(calldic['nf']) <= 34)
        elif runtime == 60:
            self.assertTrue(3 <= len(calldic['tf']) <= 5)
            self.assertTrue(10 <= len(calldic['da']) <= 12)
            self.assertTrue(9 <= len(calldic['db']) <= 11)
            self.assertTrue(13 <= len(calldic['dqr']) <= 15)
            self.assertTrue(16 <= len(calldic['nf']) <= 18)
        else:
            pass

        def _genTdif(aa: List[float]) -> List[Tuple[float, ...]]:
            result: List[Tuple[float, ...]] = []
            for _ in range(1, len(aa)):
                result.append((aa[_ - 1], aa[_], aa[_] - aa[_ - 1]))
            return result

        def _genTimes(aa: List[str]) -> List[float]:
            result: List[float] = []
            for _v in aa:
                if 't=' in _v:
                    _w = _v.split('t=', 1)
                    _wf = float(_w[1])
                    result.append(_wf)
            return result

        def _trimstartend(dic: Dict[str, float], keys: List[str]):
            for k in keys:
                if k not in dic.keys():
                    continue
                dic[k] = dic[k][1:-1]

        def _checktiming(d1: Dict[str, float], d2: Dict[str, float]) -> bool:
            result = True
            for k in d1.keys():
                result = result and d1[k] == d2[k]

            return result

        def _avragedict(timeddic) -> Dict[str, float]:
            result = {}
            for k, v in timeddic.items():
                kk = [_[2] for _ in v]
                s = sum(kk)
                result[k] = round(s / len(kk), 2)
            return result

        def _gentimedict(cdi: Dict[str, float]) -> Dict[str, float]:
            result: Dict[str, float] = {}
            for k, v in cdi.items():
                tms: List[float] = _genTimes(v)
                difs: List[Tuple[float, ...]] = _genTdif(tms)
                result[k] = difs
            return result

        timeddic: Dict[str, float] = _gentimedict(calldic)
        timeddic: Dict[str, float] = {}
        # for k, v in calldic.items():
        #tms: List[float] = _genTimes(v)
        #difs: List[Tuple[float, ...]] = _genTdif(tms)
        #timeddic[k] = difs

        _trimstartend(timeddic, ['da', 'db', 'dqr', 'nf'])

        avgtdict: Dict[str, float] = _avragedict
        self.assertTrue(_checktiming(timesdic, avgtdict))

        a = 0

    def testx01a_multiproc_simple(self):
        """test01a_threaded_simple()

        test threads started but quick exit as no function is enabled, and that basic queue
        operations work as expected

        """
        return
        print('\ntest01a_threaded_simple\n', end="")
        clearstopevents()
        reset_queues()

        bollst = [False, False, False, False, False]
        bc = sum([1 for _ in bollst if _]) + 1

        barrier = ctx.Barrier(bc)

        while (True):
            futures = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                futures = startThreads(
                    tpex, bollst, barrier, stopevents, queues)
                time.sleep(0.00001)
                barrier.wait(timeout=10)
                time.sleep(0.00001)
                print(
                    f'test01a_instat continuing at {str(time.monotonic())}\n', end="")
                # trackerstarted = time.monotonic()

                dpQ_OUT = queues['dpQ']
                dpQ_IN = queues['dpQ']

                # put 5 items on the out queue
                [dpQ_OUT.put(_) for _ in range(5)]
                # wait a second with 4 chances to do a thread switch
                [time.sleep(0.25) for _ in range(4)]

                dpqouts = dpQ_OUT.qsize()
                dpqins = dpQ_IN.qsize()
                self.assertEqual(5, dpqouts)
                self.assertEqual(dpqins, dpqouts)

                # check all threads are done
                [self.assertTrue(_.done()) for _ in futures.values()]
                try:
                    while True:
                        dpQ_IN.get_nowait()
                        dpQ_IN.task_done()
                except QEmpty:
                    pass
                dpqouts = dpQ_OUT.qsize()
                dpqins = dpQ_IN.qsize()
                self.assertEqual(0, dpqouts)
                self.assertEqual(dpqins, dpqouts)

                pass  # exit out of tpex
            break  # break out of while
        trackermain.shutdown(futures, queues, stopevents)
        barrier.reset()
        print('test01a_threaded_simple -- end\n', end="")

    def testx01b_threaded_simple(self):
        """test01b_threaded_simple()

        Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        using only get_lw as the function. No transfer to another queue

        """
        return
        print('\ntest01b_threaded_simple\n', end="")
        clearstopevents()
        reset_queues()

        # trackerinitialized = time.monotonic()
        trackerstarted = None
        bollst = [True, False, False, False, False]
        bc = sum([1 for _ in bollst if _]) + 1

        barrier = ctx.Barrier(bc)
        while (True):
            futures = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                futures = startThreads(
                    tpex, bollst, barrier, stopevents, queues)
                barrier.wait(timeout=10)
                time.sleep(0.00001)
                print(
                    f'test01b_instat continuing at {str(time.monotonic())}\n', end="")
                trackerstarted = time.monotonic()
                marktime(dly=2.5, cnt=6)
                stopevents['acquireData'].set()

                while not futures.get('weather').done():
                    time.sleep(0.005)

                res = futures.get('weather').result()
                elapsedtime = time.monotonic() - trackerstarted
                self.assertAlmostEqual(15.04, elapsedtime, places=1)
                # print(elapsedtime)
                self.assertEqual(3, len(res))
                q = queues['dataQ']
                q.put(-1)
                theq = []
                while True:
                    try:
                        theq.append(q.get(True, 0.10))
                        q.task_done()
                    except QEmpty:
                        break

                self.assertEqual(
                    [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, -1], theq)
            break
        trackermain.shutdown(futures, queues, stopevents)
        barrier.reset()
        print('test01b_threaded_simple -- end\n', end="")

    def testx01c_threaded_simple(self):
        """test01c_threaded_simple()

        Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        using get_NF and get_LW as the functions. Starting both dataacquisition threads

        """
        return
        print('test0001c_threaded_simple\n', end="")
        clearstopevents()
        reset_queues()

        # trackerinitialized = time.monotonic()
        trackerstarted = None
        bollst = [True, True, False, False, False]
        bc = sum([1 for _ in bollst if _]) + 1

        barrier = ctx.Barrier(bc)
        while (True):
            futures = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                futures = startThreads(
                    tpex, bollst, barrier, stopevents, queues)
                barrier.wait(timeout=10)
                time.sleep(0.00001)
                print(
                    f'test01c_instat continuing at {str(time.monotonic())}\n', end="")
                trackerstarted = time.monotonic()

                marktime(dly=2.5, cnt=6)

                # stops both weather and noise
                stopevents['acquireData'].set()
                time.sleep(0.0001)

                while not (futures.get('weather').done() and futures.get('noise').done()):
                    time.sleep(0.005)

                resw = futures.get('weather').result()
                resn = futures.get('noise').result()

                elapsedtime = time.monotonic() - trackerstarted
                self.assertAlmostEqual(15.04, elapsedtime, places=1)
                # print(elapsedtime)

                q = queues['dataQ']
                q.put(-1)
                theq = []
                for _ in range(5):
                    while True:
                        try:
                            theq.append(q.get(True, 0.10))
                            q.task_done()
                        except QEmpty:
                            break
                    time.sleep(0.10)

                # print(theq)
                self.assertEqual(31, len(theq))
                self.assertEqual(6, len([x for x in theq if x == 0]))
                self.assertEqual(
                    6, len([x for x in theq if x == 1 or x == 10]))
                self.assertEqual(
                    6, len([x for x in theq if x == 2 or x == 20]))
                self.assertEqual(
                    6, len([x for x in theq if x == 3 or x == 30]))
                self.assertEqual(
                    6, len([x for x in theq if x == 4 or x == 40]))

                self.assertEqual(3, len(resw))
                self.assertEqual(3, len(resn))
            break
        trackermain.shutdown(futures, queues, stopevents)
        barrier.reset()
        print('test01c_threaded_simple -- end\n', end="")

    def testx01d_threaded_simple(self):
        """test01d_threaded_simple()

        Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        using get_NF, get_LW, and transfer as the functions. Starting both dataacquisition threads

        """
        return
        print('test01d_threaded_simple\n', end="")
        clearstopevents()
        reset_queues()

        # trackerinitialized = time.monotonic()
        trackerstarted = None
        bollst = [True, True, True, False, False]
        bc = sum([1 for _ in bollst if _]) + 1

        barrier = ctx.Barrier(bc)
        while (True):
            futures = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                futures = startThreads(
                    tpex, bollst, barrier, stopevents, queues)
                barrier.wait(timeout=10)
                time.sleep(0.00001)
                print(
                    f'\ntest01d_instat continuing at {str(time.monotonic())}')
                trackerstarted = time.monotonic()
                marktime(dly=2.5, cnt=6)

                # stops both weather and noise
                stopevents['acquireData'].set()
                time.sleep(0.0001)

                while not (futures.get('weather').done() and futures.get('noise').done()):
                    time.sleep(0.005)

                q = queues['dataQ']  # add the last entry to the data q
                q.put(-1)
                stopevents['trans'].set()
                time.sleep(0.00001)
                while not futures.get('transfer').done():
                    time.sleep(0.005)

                elapsedtime = time.monotonic() - trackerstarted
                self.assertAlmostEqual(25.05, elapsedtime, places=0)
                resw = futures.get('weather').result()
                resn = futures.get('noise').result()
                resr = futures.get('transfer').result()
                self.assertEqual(31, resr)

                # print(elapsedtime)
                self.assertEqual(3, len(resw))
                self.assertEqual(3, len(resn))

                q = queues['dpQ']
                theq = []
                while True:
                    try:
                        theq.append(q.get(True, 0.00010))
                        q.task_done()
                    except QEmpty:
                        break

                self.assertTrue(31 == len(theq) or 36 == len(theq))
                self.assertEqual(6, len([x for x in theq if x == 0]))
                self.assertEqual(
                    6, len([x for x in theq if x == 1 or x == 10]))
                self.assertEqual(
                    6, len([x for x in theq if x == 2 or x == 20]))
                self.assertEqual(
                    6, len([x for x in theq if x == 3 or x == 30]))
                self.assertEqual(
                    6, len([x for x in theq if x == 4 or x == 40]))
                self.assertEqual(
                    1, len([x for x in theq if x == -1]))

            break
        trackermain.shutdown(futures, queues, stopevents)
        barrier.reset()
        print('test01d_threaded_simple -- end\n', end="")

    def testx01e_threaded_simple(self):
        """test01e_threaded_simple()

        Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        using get_NF, get_LW, transfer, and dataagragator as the functions. Starting both dataacquisition threads


        """
        return
        print('test01e_threaded_simple\n', end='')
        clearstopevents()
        reset_queues()

        trackerstarted = None
        bollst = [True, True, True, True, False]
        bc = sum([1 for _ in bollst if _]) + 1

        barrier = ctx.Barrier(bc)
        while (True):
            futures = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

                futures = startThreads(
                    tpex, bollst, barrier, stopevents, queues)
                barrier.wait(timeout=100)
                time.sleep(0.00001)
                print(
                    f'test01e_instat continuing at {str(time.monotonic())}\n', end='')
                trackerstarted = time.monotonic()
                marktime(dly=2.5, cnt=6)

                # stops both weather and noise
                stopevents['acquireData'].set()
                for _ in range(10):
                    time.sleep(0.005)

                while not (futures.get('weather').done() and futures.get('noise').done()):
                    time.sleep(0.005)

                stopevents['trans'].set()
                time.sleep(0.00001)
                while not futures.get('transfer').done():
                    time.sleep(0.005)

                # add the last entry to the data processing q
                q = queues['dpQ']
                q.put(-1)
                for _ in range(6):
                    time.sleep(0.00001)
                stopevents['agra'].set()
                time.sleep(0.00001)

                while not futures.get('dataagragator').done():
                    time.sleep(0.005)

                elapsedtime = time.monotonic() - trackerstarted
                # okt = 20.0 < elapsedtime < 25.0
                # self.assertTrue(okt)
                resw = futures.get('weather').result()
                resn = futures.get('noise').result()
                resr = futures.get('transfer').result()
                resa = futures.get('dataagragator').result()
                # TODO has a timedependency in this test it sometimes fails
                self.assertEqual(30, resr)

                # print(elapsedtime)
                self.assertEqual(3, len(resw))
                # self.assertEqual(4, len(resn))

                q = queues['dbQ']

                theq = []
                while True:
                    try:
                        theq.append(q.get(True, 0.00010))
                        q.task_done()
                    except QEmpty:
                        break

                self.assertEqual(31, len(theq))
                self.assertEqual(6, len([x for x in theq if x == 0]))
                self.assertEqual(
                    6, len([x for x in theq if x == 10 or x == 100]))
                self.assertEqual(
                    6, len([x for x in theq if x == 20 or x == 200]))
                self.assertEqual(
                    6, len([x for x in theq if x == 30 or x == 300]))
                self.assertEqual(
                    6, len([x for x in theq if x == 40 or x == 400]))
                self.assertEqual(
                    1, len([x for x in theq if x == -10]))

            break
        trackermain.shutdown(futures, queues, stopevents)
        barrier.reset()
        print('test01e_threaded_simple -- end\n', end='')

    def testx02_queue_overflow(self):
        """test02_queue_overflow()

        tests that the output queue overflow technique works

        queues in trackermain have default size of 100

        """
        return
        from trackermain import CTX

        print('test02_queue_overflow\n', end='')
        clearstopevents()
        reset_queues()
        queues['dataQ'] = CTX.JoinableQueue(
            maxsize=200)  # dataQ now has max size of 200

        try:
            for _ in range(200):
                queues['dataQ'].put(_)  # prefill the dataQ queue
        except Exception as _:
            pass

        # select only transfer to run
        bollst = [False, False, True, False, False]
        bc = sum([1 for _ in bollst if _]) + 1
        # set barrier to 2 threads this one and transfer (by count not by name)
        barrier = ctx.Barrier(bc)

        dpQ = queues['dpQ']
        self.assertTrue(dpQ.empty())
        readings = []
        self.assertEqual(200, queues['dataQ'].qsize())
        numreadings = 0

        futures = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            futures = startThreads(tpex, bollst, barrier, stopevents, queues)
            barrier.wait(timeout=10)  # wait for transfer to start

            print(
                f'test02_tqueue_overflow\n {str(time.monotonic())}\n', end='')
            doonce = True
            # loop until 'transfer is done executing and the qdQ is empty, transfer can end just after puting stuff on dpQ
            while not (futures['transfer'].done() and dpQ.empty()):
                try:
                    # possible thread switch
                    readings.append(dpQ.get(True, 1))
                    dpQ.task_done()
                    if doonce:
                        doonce = False
                        # after we received something from the queue we know
                        # that transfer is running so I can tell it to stop when  its input queue is empty
                        stopevents['trans'].set()

                except QEmpty:
                    pass

            # check if all elemenmts from dataQ have been received.
            numreadings = futures['transfer'].result()
            self.assertEqual(200, numreadings)
            self.assertFalse(futures['transfer'].cancelled())
            self.assertFalse(futures['transfer'].exception())
            for i in range(numreadings):
                self.assertEqual(i, readings[i])

            trackermain.shutdown(futures, queues, stopevents)

        self.assertEqual(numreadings, len(readings))
        for i in range(numreadings):
            self.assertEqual(i, readings[i])
        print('test02_queue_overflow -- end\n', end='')

    def testx003_trimdups(self):
        from localweather import LocalWeather, MyTime
        import pickle
        return
        print('test03_trimdups\n', end='')
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
