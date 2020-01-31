#!/usr/bin/env python3.7
"""
Test file for need
"""

# import datetime
from multiprocessing import freeze_support
import unittest
import multiprocessing as mp
from queue import Empty as QEmpty, Full as QFull
# from multiprocessing import queues as QS
import concurrent
import time
from collections import deque

import context
from deck import Deck
import trackermain
from trackermain import QUEUES as queues
from trackermain import RESET_QS as reset_queues
from trackermain import CTX as ctx
from trackermain import STOP_EVENTS as stopevents


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
    indata = Deck(100)
    stop_event = thread_info[2]

    def fillindata(delay=5):
        """fillindata(delay=)

        reads all data from dpQ_IN and places in the indata deque until dpQ_IN is empty
        """
        while True:
            try:  # empty rawDataW into indata
                # add data to the right of the queue
                indata.append(dpQ_IN.get(True, delay))
            except QEmpty:
                break
        time.sleep(0.001)  # provide oppertunity to switch threads

    def write2outQ():
        """write2outQ()

        raises IndexError if deque is empty
        raises QFull if the dbQ_OUT is full
        """
        try:
            pendingwrite = indata.popleft()
            dbQ_OUT.put(pendingwrite * 10)
            dpQ_IN.task_done()
        except IndexError:
            raise
        except QFull:
            raise

    doit = True
    while doit:
        fillindata()
        pendingwrite = None
        notstop = not stop_event.is_set()
        while notstop or len(indata) > 0:
            if len(indata) == 0:
                break
            try:
                while True:
                    try:
                        write2outQ()
                    except IndexError:  # indata is now empty
                        break

            except QFull:
                # put pending data on the left of the deque
                indata.appendleft(pendingwrite)
                time.sleep(0.0001)

            if stop_event.is_set() and dpQ_IN.empty():
                break

        doit = not stop_event.wait(6)

    for _ in range(10):  # get any late queued info

        fillindata(delay=0.5)
        while True:
            try:  # empty indata to dbQ_OUT
                write2outQ()
            except QEmpty:
                break
            except IndexError:
                break
            except QFull:
                pendingwrite = indata.popleft()
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

    def test01a_multiproc_simple(self):
        """test01a_threaded_simple()

        test threads started but quick exit as no function is enabled, and that basic queue
        operations work as expected

        """
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
                print(f'test01a_instat continuing at {str(time.monotonic())}\n', end="")
                #trackerstarted = time.monotonic()

                dpQ_OUT = queues['dpQ']
                dpQ_IN = queues['dpQ']

                # for i in range(5):
                # dpQ_OUT.put(i)
                # put 5 items on the out queue
                [dpQ_OUT.put(_) for _ in range(5)]
                # wait a second with 4 chances to do a thread switch
                [time.sleep(0.25) for _ in range(4)]

                # for _ in range(4):  # wait a second with 4 chances to do a thread switch
                # time.sleep(0.25)

                dpqouts = dpQ_OUT.qsize()
                dpqins = dpQ_IN.qsize()
                self.assertEqual(5, dpqouts)
                self.assertEqual(dpqins, dpqouts)

                # for v in futures.values():
                # self.assertTrue(v.done())
                # check all threads are done
                [self.assertTrue(v.done()) for v in futures.values()]
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

    def test01b_threaded_simple(self):
        """test01b_threaded_simple()

        Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        using only get_lw as the function. No transfer to another queue

        """
        print('\ntest01b_threaded_simple\n', end="")
        clearstopevents()
        reset_queues()

        #trackerinitialized = time.monotonic()
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
                print(f'test01b_instat continuing at {str(time.monotonic())}\n', end="")
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

    def test01c_threaded_simple(self):
        """test01c_threaded_simple()

        Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        using get_NF and get_LW as the functions. Starting both dataacquisition threads

        """
        print('test0001c_threaded_simple\n', end="")
        clearstopevents()
        reset_queues()

        #trackerinitialized = time.monotonic()
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
                print(f'test01c_instat continuing at {str(time.monotonic())}\n', end="")
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

    def test01d_threaded_simple(self):
        """test01d_threaded_simple()

        Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        using get_NF, get_LW, and transfer as the functions. Starting both dataacquisition threads

        """
        print('test01d_threaded_simple\n', end="")
        clearstopevents()
        reset_queues()

        #trackerinitialized = time.monotonic()
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
                print(f'\ntest01d_instat continuing at {str(time.monotonic())}')
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

    def test01e_threaded_simple(self):
        """test01e_threaded_simple()

        Checks to see if the dataQ, timed_work, barrier, and stopevent works plus fundimental timed_work operation
        using get_NF, get_LW, transfer, and dataagragator as the functions. Starting both dataacquisition threads


        """
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
                print(f'test01e_instat continuing at {str(time.monotonic())}\n', end='')
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
                #okt = 20.0 < elapsedtime < 25.0
                # self.assertTrue(okt)
                resw = futures.get('weather').result()
                resn = futures.get('noise').result()
                resr = futures.get('transfer').result()
                resa = futures.get('dataagragator').result()
                # TODO has a timedependency in this test it sometimes fails
                self.assertEqual(30, resr)

                # print(elapsedtime)
                self.assertEqual(3, len(resw))
                #self.assertEqual(4, len(resn))

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

    def test02_queue_overflow(self):
        """test02_queue_overflow()

        tests that the output queue overflow technique works

        queues in trackermain have default size of 100

        """
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

            print(f'test02_tqueue_overflow\n {str(time.monotonic())}\n', end='')
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
            for _ in range(numreadings):
                self.assertEqual(_, readings[_])

            trackermain.shutdown(futures, queues, stopevents)

        self.assertEqual(numreadings, len(readings))
        for i in range(numreadings):
            self.assertEqual(i, readings[i])
        print('test02_queue_overflow -- end\n', end='')


if __name__ == '__main__':

    freeze_support()
    unittest.main()
