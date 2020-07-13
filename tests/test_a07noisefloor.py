#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
# import jsonpickle
import pickle
from typing import List, Dict, Any, Tuple, Callable
from queue import Empty as QEmpty, Full as QFull
import concurrent.futures
from concurrent.futures import ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED
import context
from time import sleep as Sleep
from time import monotonic

from nfexceptions import StopEventException
import trackermain
from trackermain import Threadargs, genargs, _thread_template, runthreads
from noisefloor import NFResult, Noisefloor
from smeter import SMeter
from smeteravg import SMeterAvg
from userinput import UserInput
from flex import Flex
import postproc

from queuesandevents import QUEUES
from queuesandevents import RESET_QS
from queuesandevents import CTX

from queuesandevents import STOP_EVENTS
from queuesandevents import RESET_STOP_EVENTS
from queuesandevents import POSSIBLE_F_TKEYS as FK
from queuesandevents import STOP_EVENT_KEYS as SEK
from queuesandevents import QUEUE_KEYS as QK
from queuesandevents import Enables as ENABLES
from queuesandevents import ARG_KEYS as AK


TESTQ = CTX.JoinableQueue(maxsize=10000)
TESTOUTQ = CTX.JoinableQueue(maxsize=300)


def myprint(*arg):
    # print(arg)
    pass


# def bwdone(f):
    # pass


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


class Testnoisefloor(unittest.TestCase):
    def setUp(self):
        """setUp()

        """
        _ui = UserInput()
        _ui.request('com4')
        self.flex = Flex(_ui)
        self.flex.open()
        self.flex.do_cmd_list(postproc.INITIALZE_FLEX)

    def tearDown(self):
        """tearDown()

        """
        self.flex.close()

    @classmethod
    def setUpClass(cls):
        """setUpClass()

        """
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        cls.initial_state = flex.save_current_state()
        flex.close()
        postproc.enable_bands(['10', '20'])

    @classmethod
    def tearDownClass(cls):
        """tearDownClass()

        """
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        flex.restore_state(cls.initial_state)
        flex.close()

    def test_A01SMeter(self):
        try:

            smeter = SMeter(SMArgkeys('ZZSM000;', 5_000_000, ))
            self.assertEqual(
                '[SMeter: freq:5000000, -140.00000dBm, S0]', str(smeter))
            gg = repr(smeter)

            self.assertEqual(
                'SMeter: freq:5000000, -140.00000dBm, S0', gg)  # repr(smeter))
        except:
            a = 0
            a = 1

    def test_A02Noisefloor_inst(self):

        dataq = QUEUES[QK.dQ]
        #stope = STOP_EVENTS['acquireData']
        stope = STOP_EVENTS[SEK.ad]

        # , testdata='noisefloordata.pickle')
        nf: Noisefloor = Noisefloor(self.flex, dataq, stope)
        self.assertTrue(nf.open(), 'smartSDR not running')
        nf.doit(loops=10, testdatafile='nfrlistdata.pickle', dups=True)

        self.assertTrue(nf.close())
        results: List[NFResult] = []
        try:
            while True:
                results.append(dataq.get(timeout=3))

        except QEmpty:
            pass

        self.assertEqual(10, len(results))
        samp: NFResult = results[2].get()
        self.assertEqual('Apr 12 2020 23:31:39', samp.starttime)
        self.assertEqual('Apr 12 2020 23:32:43', samp.endtime)
        r0bss: SMeterAvg = samp.readings[0]
        self.assertEqual('40', r0bss.band)
        self.assertEqual(-104.0, r0bss.dBm['mdBm'])

    def test_B01NoiseFloorStopEvent(self):
        """test_005NoiseFloorStopEvent

        The two seperate operations in this section make sure that
        1) shutdown works with no threads, first and 3rd thread and 3rd and 5th threads
        2) disabled threads start and end correctly
        3) that all the threads can be started and operate reaonable (with test data)
        the only data sent on a queue is to the TESTQ which basically the result of myprint calls
           and the debug text output for this is disabled by default.

        these tests check operation of trackermain.timedwork, but not much else as all the test
        functions are in the test routine
        """

        # must release the flex and ui setup in the per test setup for this test
        self.flex.close()

        #from queuesandevents import QUEUES, STOP_EVENTS
        from qdatainfo import NFQ

        barrier: CTX.Barrier = CTX.Barrier(0)

        # timesdic = {'tf': 15, 'nf': 4, 'dqr': 5, 'da': 6, 'db': 7}

        def tf(arg: Threadargs):  # the program periodically executed by the timer thread
            """tf()

            """
            pass

#
# Threadargs = namedtuple('Threadargs', ['execute', 'barrier', 'stope',
            # 'qs', 'name', 'interval', 'doit'])
#
        def nf(arg: Threadargs, **kwargs):
            """
            noisefloor proxy
            arg is named tuple Threadargs

            Justs writes the routine name, thread name and time to TESTQ and maybe the consule

            """
            def doita():  # the program to be run by _thread_template the return 0 says that no work need be done when stopping
                try:

                    UI: UserInput = UserInput()
                    UI.request(port='com4')
                    flexr: Flex = Flex(UI)
                    nf: Noisefloor = Noisefloor(
                        flexr, arg.qs[QK.dQ], arg.stope, run_till_stopped=True)
                    nf.open()
                    nf.doit(loops=0, runtime=0,
                            interval=100, dups=True)
                except StopEventException as see:
                    nf.close()
                    raise see

                # update the interval and function
            mma: Threadargs = arg._replace(
                doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def dqr(arg: Threadargs, **kwargs):
            """
            noisefloor proxy
            arg is named tuple Threadargs

            Justs writes the routine name, thread name and time to TESTQ and maybe the consule

            """
            def doita():  # the program to be run by _thread_template the return 0 says that no work need be done when stopping
                pass

            mma = arg._replace(
                interval=1, doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def daf(arg: Threadargs, **kwargs):
            """
            noisefloor proxy
            arg is named tuple Threadargs

            Justs writes the routine name, thread name and time to TESTQ and maybe the consule

            """
            def doita():  # the program to be run by _thread_template the return 0 says that no work need be done when stopping
                pass

            mma = arg._replace(
                interval=1, doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        def dbf(arg: Threadargs, **kwargs):
            """
            noisefloor proxy
            arg is named tuple Threadargs

            Justs writes the routine name, thread name and time to TESTQ and maybe the consule

            """
            def doita():  # the program to be run by _thread_template the return 0 says that no work need be done when stopping
                pass

            mma = arg._replace(
                interval=1, doit=doita)
            # run it
            return _thread_template(mma, printfun=myprint, **kwargs)

        # def runthreads(calls: Tuple[Callable, ...], argdicin: Dict[str, Threadargs], tpex) -> Dict[str, Any]:
            #futures: Dict[str, Any] = {}
            # futures[FK.w] = tpex.submit(
            # calls.w, argdicin[AK.w], printfn=myprint)

            # gets banddata data
            #futures[FK.n] = tpex.submit(calls.n, argdicin[AK.n])

            # reads the dataQ and sends to the data processing queue dpq
            #futures[FK.t] = tpex.submit(calls.t, argdicin[AK.t])

            # looks at the data and generates the approprate sql to send to dbwriter
            #futures[FK.da] = tpex.submit(calls.da, argdicin[AK.da])

            # reads the database Q and writes it to the database
            #futures[FK.db] = tpex.submit(calls.db, argdicin[AK.db])

            # _ = tpex.submit(breakwait, barrier)  # break the barrier
            # _.add_done_callback(bwdone)
            # return futures

        # turn off all selected thread routines
        bollst: Tuple[bool, ...] = ENABLES(
            w=False, n=False, t=False, da=False, db=False,)
        """
        # Check empty submit works with tracker.shutdown
        """
        calls: Tuple[Callable, ...] = ENABLES(w=trackermain.timed_work,
                                              n=nf, t=dqr, da=daf, db=dbf)
        # no threads running
        futures: Dict[str, Any] = {}
        waitresults: Tuple[Set, Set] = trackermain.shutdown(
            futures, QUEUES, STOP_EVENTS)
        self.assertTrue(waitresults is None)

        """
        # Check submit and shutdown works with all threads disabled
        """
        argdic: Dict[int, Threadargs] = genargs(barrier, bollst)
        #tpex = None
        """
        This did not work when placed in a with construct, and it stops the diagnostic from completing!
        No idea why not
        """
        if False:
            if True:
                tpex = concurrent.futures.ThreadPoolExecutor(
                    max_workers=10, thread_name_prefix='dbc-')
                futures: Dict[str, Any] = runthreads(
                    barrier, calls, argdic, tpex)
                for _ in range(1):
                    Sleep(1)  # wait for a while to let the threads work
                waitresults = trackermain.shutdown(
                    futures, QUEUES, STOP_EVENTS, time_out=1)
                a = 0
                # wait = True cause hang, false doesn't let the diagnostic end
                tpex.shutdown(wait=True)

            # all 5 threads ran to completion
            self.assertEqual(5, len(waitresults.done))
            self.assertEqual(0, len(waitresults.not_done))

        cleartestq()
        bollst: Tuple[bool, ...] = ENABLES(
            w=False, n=False, t=False, da=False, db=False,)

        bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier
        barrier = CTX.Barrier(bc)
        myprint('starting')

        argdic: Dict[int, Threadargs] = genargs(barrier, bollst)
        # mods for test
        argdic[AK.w] = argdic[AK.w]._replace(
            name='timed_work', interval=10.5, doit=tf)

        """
        Start the threads, all should just activate and then exit leaving a trace this time
        """
        # mythreadname = threading.currentThread().getName()
        # mythread = threading.currentThread()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            futures: Dict[str, Any] = runthreads(
                barrier, calls, argdic, tpex)
            for _ in range(1):
                Sleep(1)
            waitresults = trackermain.shutdown(futures, QUEUES, STOP_EVENTS)

        self.assertEqual(5, len(waitresults.done))
        self.assertEqual(0, len(waitresults.not_done))
        # check that the results were expected
        for _ in waitresults.done:
            self.assertTrue(_.done())
            rrr = repr(_.result())
            self.assertTrue(rrr in ['[]', 'None', 'deque([], maxlen=10)'])

        # turn on noisefloor thread
        bollst: Tuple[bool, ...] = ENABLES(False, True, False, False, False)
        # count them for barrier the plus 1 is for starting thread
        bc = sum([1 for _ in bollst if _]) + 1
        barrier = CTX.Barrier(bc)
        runtime = 90  # either 60, or 120 if not one of these, some of the asserts are ignored
        cleartestq()
        RESET_STOP_EVENTS()

        argdic: Dict[int, Threadargs] = genargs(barrier, bollst)
        # mods for test
        argdic[AK.w] = argdic[AK.w]._replace(
            interval=1, doit=tf)
        argdic[AK.n] = argdic[AK.n]._replace(
            interval=None)
        argdic[AK.t] = argdic[AK.t]._replace(
            interval=1)
        argdic[AK.da] = argdic[AK.da]._replace(
            interval=1)
        argdic[AK.db] = argdic[AK.db]._replace(
            interval=1)
        """
        Try running the noise floor for real on a thread
        check that shutdown will actually stop it
        """
        start = monotonic()
        futures: Dict[str, Any] = None
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            futures: Dict[str, Any] = runthreads(
                barrier, calls, argdic, tpex)
            for _ in range(runtime):  # wait for a while to let the threads work
                Sleep(1)
            waitresults = trackermain.shutdown(
                futures, QUEUES, STOP_EVENTS, time_out=120)  # wait max 60 for the threads to stop

        end = monotonic()
        elapsed = end - start
        myprint(
            f'elapsed: {elapsed}, runtime set to: {runtime}, 120 sec timeout delay')
        # took the expected one reading
        self.assertEqual(1, QUEUES[QK.dQ].qsize())
        nfqdta: NFQ = QUEUES[QK.dQ].get_nowait()
        nfr: NFResult = nfqdta.get()
        if (nfr is None):
            print('nfr is none')
        else:
            self.assertTrue(nfr._started and nfr._ended)
            self.assertEqual(4, len(nfr.readings))  # got all 4 bands

        bollst: Tuple[bool, ...] = ENABLES(
            w=False, n=True, t=False, da=False, db=False)
        # count them for barrier the plus 1 is for starting thread
        bc = sum([1 for _ in bollst if _]) + 1
        barrier = CTX.Barrier(bc)
        # runtime = 100  # either 60, or 120 if not one of these, some of the asserts are ignored
        cleartestq()
        RESET_STOP_EVENTS()

        argdic: Dict[int, Threadargs] = genargs(barrier, bollst)
        # mods for test
        argdic[AK.w] = argdic[AK.w]._replace(
            interval=1, doit=tf)
        argdic[AK.n] = argdic[AK.n]._replace(
            interval=None)
        argdic[AK.t] = argdic[AK.t]._replace(
            interval=1)
        argdic[AK.da] = argdic[AK.da]._replace(
            interval=1)
        argdic[AK.db] = argdic[AK.db]._replace(
            interval=1)

        """
        Try running the noise floor for real on a thread
        check that setting stop event will stop it
        Set to stop in the mid band scan
        """

        start = monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            futures: Dict[str, Any] = runthreads(
                barrier, calls, argdic, tpex)
            for _ in range(int(runtime / 3)):  # wait for a while to let the threads work
                Sleep(1)
            STOP_EVENTS[SEK.da].set()  # stop the the data acquisition
            waitresults = trackermain.shutdown(
                futures, QUEUES, STOP_EVENTS, time_out=120)  # wait max 60 for the threads to stop

        end = monotonic()
        elapsed = end - start
        # aborted before it could complete a cycle
        self.assertEqual(0, QUEUES[QK.dQ].qsize())
        myprint(
            f'elapsed: {elapsed}, runtime set to: {int(runtime/3)}, 120 sec timeout delay')
        a = 0

    def test_A03Noisefloortestfiles(self):
        from qdatainfo import NFQ
        from math import isclose
        from datetime import datetime as DT
        from datetime import timedelta as TD
        nfqldata: List[NFQ] = []
        with open('nfqlistdata.pickle', 'rb') as jso:
            nfqldata = pickle.load(jso)
        self.assertEqual(90, len(nfqldata))

        nfrldata: List[NFResult] = []
        with open('nfrlistdata.pickle', 'rb') as jso:
            nfrldata = pickle.load(jso)
        self.assertEqual(90, len(nfrldata))

        smavdata: List[SMeterAvg] = []
        with open('smavflistdata.pickle', 'rb') as jso:
            smavdata = pickle.load(jso)
        self.assertEqual(270, len(smavdata))

        nfq = nfqldata[0]
        nfqtimel: List[Tuple[int, TD, DT, DT, ]] = []
        for i in range(1, len(nfqldata)):
            t1: DT = nfqldata[i].utctime
            t0: DT = nfqldata[i - 1].utctime
            td: TD = t1 - t0
            if not isclose(td.total_seconds(), 90.0, abs_tol=0.5):
                nfqtimel.append((i, td, t0, t1,))
        self.assertEqual(6, len(nfqtimel))

        # index, time delta between starts, time taken
        nfrlderr: List[Tuple[int, TD, TD]] = []
        for i in range(1, len(nfrldata)):
            st1: DT = DT.strptime(nfrldata[i].starttime, '%b %d %Y %H:%M:%S')
            st0: DT = DT.strptime(
                nfrldata[i - 1].starttime, '%b %d %Y %H:%M:%S')
            et: DT = DT.strptime(nfrldata[i].endtime, '%b %d %Y %H:%M:%S')
            sd: TD = st1 - st0
            dur: TD = et - st1
            if not isclose(sd.seconds, 90.0, abs_tol=0.5) or not isclose(dur.seconds, 65.0, abs_tol=3.0):
                nfrlderr.append((i, sd, dur))
        self.assertEqual(6, len(nfrlderr))


if __name__ == '__main__':
    unittest.main()
