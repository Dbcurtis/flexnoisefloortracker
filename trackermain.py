#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os


# from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque
from typing import Any, Tuple, List, Dict, Deque

from queue import Empty as QEmpty, Full as QFull
import concurrent.futures
import multiprocessing as mp
from queuesandevents import CTX, QUEUES, STOP_EVENTS
import logging
import logging.handlers
import pickle

from time import sleep as Sleep
from time import monotonic
from datetime import datetime as Dtc
from datetime import timezone
from collections import deque

from deck import Deck
from localweather import LocalWeather
import threading
from userinput import UserInput
from nfresult import NFResult

from flex import Flex
# from noisefloor import Noisefloor
# from qdatainfo import DataQ, DbQ, DpQ, LWQ


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/trackermain'

EXITING = False


class Consolidate:
    def __init__(self):
        pass

    def __str__(self):
        return 'no str yet'

    def __repr__(self):
        return 'no repr yet'

    def doit(self, datalst):
        pass


class DBwriter:
    """DBwriter(thread_info)

    thread_info = (execute, barrier, stop_event, queues)
    """

    def __init__(self, thread_info):
        self.dpQ_IN: CTX.JoinableQueue = thread_info[3]['dbQ']
        self.execute: bool = thread_info[0]
        self.barrier: CTX.Barrier = thread_info[1]
        self.stop_event: CTX.Event = thread_info[2]

    def run(self):
        """run()

        """
        if not self.execute:
            return

        indata: Deck = Deck(100)  # deque([])
        # self.barrier.wait()

        print ('DBwriter started')

        while not self.stop_event.wait(10):
            while True:
                try:
                    # add data to the right of the deque
                    indata.append(self.dpQ_IN.get(True, 10))
                    self.dpQ_IN.task_done()
                except QEmpty:
                    break

            sqlcmdlst = self.consolidate.doit(indata)
            pendingwrite = None

            while True:
                try:
                    pendingwrite = sqlcmdlst.popleft()
                    self.dbQ_OUT.put(pendingwrite)

                except IndexError:  # indata is now empty
                    break

                except QFull:
                    # put pending data on the left of the sqlcmdlst
                    sqlcmdlst.appendleft(pendingwrite)
                    Sleep(10)

            if self.stop_event.is_set():
                break
        print('dataQ_reader ended')
        return []


def jjj():
    pass


class Aggratator:
    """Aggratator(thread_info)

    thread_info = (execute, barrier, stop_event, queues)
    """

    def __init__(self, thread_info, aggfn=jjj):
        self.dpQ_IN: CTX.JoinableQueue = thread_info[3]['dpQ']
        self.dbQ_OUT: CTX.JoinableQueue = thread_info[3]['dbQ']
        self.execute: bool = thread_info[0]
        self.barrier = thread_info[1]
        self.stop_event: CTX.Event = thread_info[2]
        self.consolidate = Consolidate()
        self.fn = aggfn

    def run(self):
        """run()

        """
        if not self.execute:
            return 0
        count = [0]
        # self.barrier.wait()

        print ('Aggratator started')

        deck = Deck(50)
        while True:
            # while not self.stop_event.wait(10):
            while True:
                try:
                    deck.load_from_Q(self.dpQ_IN, True)

                except QFull:  # if deck has reached its max
                    break

                finally:
                    sqlcmdlst = self.consolidate.doit(deqPrams)
                    pendingwrite = None

                    while True:
                        try:
                            pendingwrite = sqlcmdlst.popleft()
                            # self.dbQ_OUT.put(pendingwrite)
                            self.fn(self.dbQ_OUT, pendingwrite)
                            count += 1

                        except QFull:
                            # put pending data on the left of the sqlcmdlst
                            sqlcmdlst.appendleft(pendingwrite)
                            Sleep(10)

                        except IndexError:  # indata is now empty
                            break

            if self.stop_event.is_set():
                break
        print('dataQ_reader ended')
        return [count]


def dataaggrator(thread_info, aggfn=None, debugfn=None):
    """dataaggrator(thread_info, debugfn=None)

    this is the 'dataagragator' thread in futures

     thread_info is (execute, barrier, stop_event, queues,),

    """
    if debugfn:
        return debugfn(thread_info)

    else:
        ag = Aggratator(thread_info, aggfn)
        return ag.run()


def Get_LW1(rawDataQ_OUT):
    times: str = str(Dtc.now(timezone.utc))
    rawDataQ_OUT.put(times)


def Get_LW(rawDataQ_OUT):
    """Get_LW(rawDataQ_OUT)

    Gets Local Medfrod weather in a LocalWeather object and adds it to the rawDataQ_OUT queue.

    """
    from qdatainfo import LWQ
    _lw = LocalWeather()
    _lw.load()
    parital_sql: str = _lw.gen_sql()
    pkg: LWQ = LWQ(parital_sql)
    rawDataQ_OUT.put(pkg)

    # rawDataQ_OUT.put(_lw)


def Get_NF(rawDataQ_OUT):
    """Get_NF(rawDataQ_OUT)

    """
    from noisefloor import Noisefloor
    UI = UserInput()
    NOISE = None
    try:
        UI.request(port='com4')
        UI.open()
        print("Requested Port can be opened")
        FLEX = Flex(UI)
        NOISE = Noisefloor(FLEX, rawDataQ_OUT)
        NOISE.open()
        NOISE.doit(loops=10, interval=30)
        NOISE.close()

    except(Exception, KeyboardInterrupt) as exc:
        if NOISE:
            NOISE.close()
        UI.close()
        sys.exit(str(exc))

    finally:
        if NOISE:
            NOISE.close()
        UI.close()
        sys.exit(str(exc))
    _nf = NoiseFloor()


# def load_deque(deqPrams, inQ, markdone):
    # deck = deqPrams[0]
    # deck.load_from_Q(inQ, mark_done=markdone)
    # deqPrams[2][0] = len(deck)


# def write_2_q(outQ, data):
    # outQ.put(data, False)
def trim_dups(mydeck, boolfn):
    if not mydeck:
        return []
    lst = list(mydeck)
    tuplst = [(boolfn(lst[i], lst[i + 1]), lst[i], lst[i + 1],)
              for i in range(len(lst) - 1)]
    return tuplst


def get_noise(*args):
    """

    *args is (execute, barrier, stop_event, queues,)
    """
    from flex import Flex
    from postproc import BANDS, BandPrams, INITIALZE_FLEX
    from noisefloor import Noisefloor
    queues: Dict[str, Any] = args[3]
    stop_event = args[2]
    resultQ = queues['dataQ']
    barrier = args[1]

    if args[0]:  # execute:
        # barrier.wait()
        print('get_noise started\n', end="")
        UI: UserInput = UserInput()
        nf: Noisefloor = None

        UI.request(port='com4')
        flexr: Flex = Flex(UI)
        print('saving flex state')
        initial_state = flexr.save_current_state()
        try:
            if not flexr.open():
                raise (RuntimeError('Flex not connected to serial serial port'))

            nf = Noisefloor(flexr, resultQ, stop_event)
            nf.open()
            nf.doit(loops=0, interval=90, runtime=0, dups=True)

        finally:
            print('restore flex prior state')
            flexr.restore_state(initial_state)

            if nf:
                nf.close()
            UI.close()

    print('get_noise ended\n', end="")
    return


# -----------------------


# try:
    # if not flexr.open():
    # raise (RuntimeError('Flex not connected to serial serial port'))
    # print('saving current flex state')
    # initial_state = flexr.save_current_state()
    # print('initializing dbg flex state')
    # flexr.do_cmd_list(INITIALZE_FLEX)
    # flexr.close()
    # resultQ = queues.get('dataQ')
    # stop_event = stop_events.get('acquireData')

    # NOISE = Noisefloor(flexr, resultQ, stop_event)
    # NOISE.open()
    # loops must be less than 100 as that is the queue size and I am not emptying it here
    # NOISE.doit(loops=90, interval=90, dups=True)
    # NOISE.doit(runtime=1, interval=60)
    # stop_event.set()

    # indata: List[NFQ] = []

    # a = indata[0]
    # b = outdata[0]

# except(Exception, KeyboardInterrupt) as exc:
    # if NOISE:
    # NOISE.close()
    # UI.close()
    # raise exc

# finally:
    # print('restore flex prior state')
    # flexr.restore_state(initial_state)

    # if NOISE:
    # NOISE.close()
    # UI.close()


# ---------------------
# write_2_q):


# , fn=lambda outQ, data: outQ.put(data, False)):
def dataQ_reader_datagen(*args, **kwargs):
    """

    this is the 'transfer' thread in futures for the datagen1 main routine

     *args is (execute, barrier, stop_event, queues,)
    """
    ti_dict: Dict[str, Any] = {}
    ti_dict['execute'] = args[0]
    ti_dict['barrier'] = args[1]
    ti_dict['stop_event'] = args[2]
    ti_dict['queues'] = args[3]

    if ti_dict['execute']:  # execute:

        locald = threading.local()

        locald.rawDataQ_IN = ti_dict['queues']['dataQ']

        locald.count = 0
        # ti_dict['barrier'].wait()  # wait for the barrier
        print('dataQ_reader_datagen started\n', end="")
        # the deque, max size, single element  size inititally 0
        # locald.deqPrams = (Deck(50), 50, [0])
        indeck = Deck(100)

        while True:
            try:  # empty rawDataW into indata
                # waits for 10sec to try to empty Q
                indeck.load_from_Q(locald.rawDataQ_IN, mark_done=True)

            except QFull:  # the deck is full
                print(f'indeck is full {len(indeck)}')

            finally:
                if len(indeck) >= 20:  # deck is 100 so this should work w/o problems
                    break

        templst: List[Any] = []
        try:
            while True:
                templst.append(indeck.popleft())
        except IndexError:
            pass  # indeck now wmpty
        with open('localweathersqlshort.pickle', 'wb') as fl:
            try:
                pickle.dump(templst, fl)
            except Exception as ex:
                a = 0

        print('dataQ_reader_datagen ended\n', end="")
        return locald.count

    pass


def dataQ_reader(*args, **kwargs):
    """dataQ_reader(*args, **kwargs)

    this is the 'transfer' thread in futures

     *args is (execute, barrier, stop_event, queues,),
     'fn' in kwargs is the function to be applied to the input data and defaults to writing data
     to the outQ

    """
    locald = threading.local()
    locald.ti_dict: Dict[str, Any] = {}
    locald.ti_dict['execute'] = args[0]
    locald.ti_dict['barrier'] = args[1]
    locald.ti_dict['stop_event'] = args[2]
    locald.ti_dict['queues'] = args[3]
    locald.fn = None
    try:
        locald.fn = kwargs['fn']
    except KeyError:
        pass

    if locald.ti_dict['execute']:  # execute:
        import localweather

        locald.rawDataQ_IN = locald.ti_dict['queues']['dataQ']
        locald.dpQ_OUT = locald.ti_dict['queues']['dpQ']
        locald.stop_event = locald.ti_dict['stop_event']
        locald.count = 0
        locald.ti_dict['barrier'].wait()
        for _ in range(10):
            Sleep(0.0001)
        print('dataQ_reader started\n', end="")
        # the deque, max size, single element  size inititally 0
        # locald.deqPrams = (Deck(50), 50, [0])
        locald.indeck = Deck(100)
        locald.wetherdec = Deck(100)
        locald.noisedeck = Deck(100)
        locald.lastweather = None
        locald.lastnoise = None

        while True:

            try:  # empty rawDataW into indata
                locald.indeck.load_from_Q(
                    locald.rawDataQ_IN, mark_done=False)

            except QFull:
                pass

            finally:
                if len(locald.indeck) > 0:

                    locald.wetherdec.clear()
                    locald.wetherdec.push(locald.lastweather)
                    locald.noisedeck.clear()
                    locald.noisedeck.push(locald.lastnoise)
                    # separate the indeck contents
                    try:
                        while(len(locald.indeck) > 0):
                            cnt = locald.indeck.popleft()
                            if isinstance(cnt, LocalWeather):
                                locald.wetherdec.append(cnt)
                            elif isinstance(cnt, NFResult):
                                locald.noisedeck.append(cnt)
                            else:
                                raise AssertionError("need to handle")
                    except IndexError:
                        pass
                    finally:
                        pass
                    data_tobe_processed = None
                    locald.tuplst = trim_dups(
                        locald.wetherdec, localweather.different)

                    locald.noiselist = list(locald.noisedeck)
                    locald.noisemarkers = [i for i in range(1, len(weatherlist)) if
                                           (weatherlist[i - 1].has_changedweatherlist[i])]

                    # first item of wetherdec and noisedeck may be None!
                while True:
                    try:
                        while True:
                            # data_tobe_processed = locald.deqPrams[0] \
                                # .popleft()
                            locald.data_tobe_processed = indeck.popleft(
                            )
                            # process the data
                            locald.fn(locald.dpQ_OUT, data_tobe_processed)
                            locald.deqPrams[2][0] = locald.deqPrams[2][0] - 1
                            locald.rawDataQ_IN.task_done()
                            locald.count += 1

                    except QFull:
                        # put pending data on the left of the queue
                        # locald.deqPrams[0].appendleft(data_tobe_processed)
                        locald.deqPrams[0].push(data_tobe_processed)
                        Sleep(10)

                    except IndexError:  # indata is now empty
                        break
            # things look done
            if locald.stop_event.wait(5.0):
                if locald.rawDataQ_IN.empty() and len(locald.deqPrams[0]) == 0:
                    break

        print('dataQ_reader ended\n', end="")
        return locald.count


def read_inQ_2deque():
    result = True
    return result


def writesql():
    pass


def dbQ_writer(thread_info, debugfn=None):
    """dbQ_writer(thread_info, debugfn=None)

    thread_info = (execute, barrier, stop_event, queues,),

    execute is a boolean which if true causes the function to operate if false, just to end
    barrier is a Barrier to make sure everything is ready at the same time
    stop_event is set if we are in the process of shutting down
    queues is a dict of joinablequeues one of which must be 'dbQ'
    debugfn is a function that will be invoked (used for debugging) to process each entry in the 'dbQ'

    """

    if debugfn:
        return debugfn(thread_info)

    else:
        ag = Aggratator(thread_info)
        return ag.run()

    if thread_info[0]:
        doit = writesql
        if debugfn:
            doit = debugfn

        dbQIN = thread_info[3]['dbQ']
        print('dbQ_writer waiting\n', end='')
        thread_info[1].wait()
        print('dbQ_writer started\n', end='')
        stop_event = thread_info[2]

        sqldata = deque([])

        while not stop_event.wait(10):
            while True:
                try:
                    # add data to the right of the queue
                    sqldata.append(dbQIN.get(True, 10))
                except QEmpty:
                    pass
                try:
                    while True:
                        pendingwrite = sqldata.popleft()
                        doit(pendingwrite)
                        dbQIN.task_done()
                except IndexError:  # sqldata is now empty
                    break

            if stop_event.is_set():
                break
        print('dbQ_writer ended\n', end='')


# def timed_work(execute, barrier, stop_event, queues, delayseconds, fu):
def timed_work(*args, **kwargs):  # thread_info, delayseconds, fu):
    """timed_work(thread_info, delayseconds, fu, )

    *args is (execute, barrier, stop_event, queues),
    execute is a boolean that if True will actually execute fu
    barrier is used to coordinate starting the tasks/threads
    stop_event if set causes the task/thread to stop

    **kwargs is
    'delay' is the number of seconds between calls to fu
    'timed_func' is the function that will be called on the time basis

    will continue forever until the stop event

    queues is the queue dict, but timed_work only uses 'dataQ' from the dict

    this is used for the weather thread

    """

    # class Sequencer:
    # """Sequencer(delayseconds:float)

    # Sets up a 20 repretition delayseconds apart  The repetition stays at 20
    # resolution is about .5 second (not checked, but guessed)
    # """

    # def __init__(self, delayseconds: float):
    #self.delayseconds = delayseconds
    #nowis = monotonic()
    # self.to_do_sched: Deque[float] = deque(
    # [nowis + t * delayseconds for t in range(1, 21)])  # specifies the first 20 repes

    # def do_it_now(self) -> bool:
    # """ do_it_now()

    # Decides if it is time to do something on a todo schedule
    # """
    # if self.to_do_sched[0] > monotonic():  # if next scheuled is not yet os
    # return False

    # for each schedled time < current,
    # while self.to_do_sched[0] < monotonic():
    # self.to_do_sched.popleft()   # remove the scheduled time that is os
    # and add another scheduled time in the future.
    # self.to_do_sched.append(
    # self.to_do_sched[-1] + self.delayseconds)

    # return True

    # def get_nxt_wait(self) -> float:
    # """get_nxt_wait()

    # """
    # nextt: float = self.to_do_sched[0]
    #nextt -= monotonic() * 1.1
    #nextt = 0 if nextt < 0 else nextt
    # return nextt
    from sequencer import Sequencer
    locald = threading.local()
    ti_dict: Dict[str, Any] = {}
    ti_dict['execute'] = args[0]
    ti_dict['barrier'] = args[1]
    ti_dict['stop_event'] = args[2]
    ti_dict['queues'] = args[3]

    print('timed work invoked')
    if ti_dict['execute']:
        # locald = threading.local()
        locald.execute = ti_dict['execute']
        locald.raw_data_Q = ti_dict['queues']['dataQ']
        locald.stop_event = ti_dict['stop_event']
        locald.delayseconds = kwargs['delay']
        locald.fu = kwargs['timed_func']

        locald.last10executtimes = deque([], 10)  # queue of max length 10
        # print('timed_work waiting to pass barrier\n',end="")
        # ti_dict['barrier'].wait()  # barrier pass
        # for _ in range(10):
        # Sleep(0.0001)
        print(f'timed_work started: {monotonic()}\n', end="")

        locald.seq = Sequencer(locald.delayseconds)
        while not locald.stop_event.wait(0.45):
            if locald.seq.do_it_now():
                locald.last10executtimes.append(f'{str(Dtc.now().time())}, {str(locald.fu)}')
                # print(locald.last10executtimes)
                locald.fu(locald.raw_data_Q)
            # Sleep(0.00001)  # context switch oppertunity

            if locald.stop_event.is_set():
                break
        print(f'timed_work ended: {time.monotonic()}\n', end="")
        return(locald.last10executtimes)


def shutdown(futures, queues, stopevents):
    """shutdown(futures, queues, stopevents)

    """
    # stop the data generating processes
    stopevents['acquireData'].set()
    stopevents['trans'].set()
    validkeys = list(futures.keys())

    # isdone = True
    # keys are the dict keys for data generation threads
    # selected from weather noise transfer dataagragator dbwriter
    keys = [k for k in validkeys if k in ('weather', 'noise',)]

    while True:
        Sleep(0.001)
        bb = [futures[k].done() for k in keys]

        cc = [v for v in bb if v]
        if len(cc) == len(bb):
            break

    # wait until the dataQ fileed by the data generating processes empty
    while not queues['dataQ'].empty():
        Sleep(0.001)

    # the dataQ is empty now ok to stop the datareader
    stopevents['trans'].set()
    if 'transfer' in validkeys:
        while not futures['transfer'].done():
            Sleep(0.001)

    # stop the data aggragator
    stopevents['agra'].set()
    if 'dataagragator' in validkeys:
        while not futures['dataagragator'].done():
            Sleep(0.001)

    while not queues['dpQ'].empty():
        Sleep(0.001)
    # stop the data base writer
    stopevents['dbwrite'].set()
    if 'dbwriter' in validkeys:
        while not futures['dbwriter'].done():
            Sleep(0.001)


def main(hours: float = 0.5):
    """main(hours=0.5)

    """

    queues = QUEUES
    timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)

    # enable all the threads
    bollst: List[bool] = [True, True, True, True, True]
    bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier

    barrier: CTX.Barrier = CTX.Barrier(bc)

    trackerinitialized: float = monotonic()  # returns seconds
    trackerTimeout: float = trackerinitialized + timetup[2]

    """
        'delay' is the number of seconds between calls to fu
    'timed_func' is the function that will be called on the time basis
    """

    trackerstarted = None
    while (True):
        futures: Dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            futures = {
                # gets weather data
                'weather': tpex.submit(timed_work, bollst[0], barrier, STOP_EVENTS['acquireData'], queues, delay=60 * 10.5, timed_func=Get_LW),
                # gets banddata data
                # 'noise': tpex.submit(timed_work, bollst[1], barrier, STOP_EVENTS['acquireData'],queues, 'delay'=60, Get_NF),
                'noise': tpex.submit(get_noise, bollst[1], barrier, STOP_EVENTS['acquireData'], queues),
                # reads the dataQ and sends to the data processing queue dpq
                # fn is wrong
                'transfer': tpex.submit(dataQ_reader, bollst[2], barrier, STOP_EVENTS['trans'], queues, fn=None),
                # looks at the data and generates the approprate sql to send to dbwriter
                'dataagragator': tpex.submit(dataaggrator, bollst[3], barrier, STOP_EVENTS['agra'], queues),
                # reads the database Q and writes it to the database
                'dbwriter': tpex.submit(dbQ_writer, bollst[4], barrier, STOP_EVENTS['dbwrite'], queues),

            }

        for _ in range(10):  # let things start and reach the waiting state
            Sleep(0.001)
            # barrier.wait()  # start them all working
            trackerstarted: float = monotonic()
            trackerschedend: float = trackerstarted + timetup[2]
            monotonic() < trackerschedend
            while monotonic() < trackerTimeout:
                Sleep(5)
            shutdown(futures, queues, STOP_EVENTS)
            break  # break out of tpex
        a = 0
        break  # break out of while loop
    return


def datagen3(hours: float = 0.5):
    """datagen3(hours=0.5)

    """
    tsi = sys.getswitchinterval()
    # sys.setswitchinterval(3)

    queues = QUEUES
    dq = queues['dataQ']
    timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)

    # turn on selected threads
    bollst: Tuple[bool] = (True, True, True, False, False)
    bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier

    barrier: CTX.Barrier = CTX.Barrier(bc)

    trackerinitialized: float = monotonic()  # returns seconds
    trackerTimeout: float = trackerinitialized + timetup[2]

    trackerstarted = None
    tempdec: Deck = Deck(30)

    while (True):
        futures: Dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            try:

                futures = {
                    # gets weather data
                    'weather': tpex.submit(timed_work, bollst[0], barrier, STOP_EVENTS['acquireData'], queues, delay=60 * 10.5, timed_func=Get_LW),
                    # gets banddata data
                    # #'noise': tpex.submit(timed_work, bollst[1], barrier, STOP_EVENTS['acquireData'], 60, Get_NF, queues),
                    # 'noise': tpex.submit(get_noise, bollst[1], barrier, STOP_EVENTS['acquireData'], queues),
                    # reads the dataQ and sends to the data processing queue dpq
                    # fn is wrong
                    # 'transfer': tpex.submit(dataQ_reader, bollst[2], barrier, STOP_EVENTS['trans'], queues, fn=None),
                    # looks at the data and generates the approprate sql to send to dbwriter
                    # 'dataagragator': tpex.submit(dataaggrator, bollst[3], barrier, STOP_EVENTS['agra'], queues),
                    # reads the database Q and writes it to the database
                    # 'dbwriter': tpex.submit(dbQ_writer, bollst[4], barrier, STOP_EVENTS['dbwrite'], queues),

                }
            except Exception as e:
                aa = 0

            [tempdec.append(f.running()) for f in futures.values()]
            tempdec.loadQ(dq)
            dataQDeque: Deck = Deck(10000)
            print('main waiting for start')
            for _ in Range(200):
                ss = [(k, v) for k, v in futures.items()]
                Sleep(1)

            # barrier.wait()  # start them all working
            print('main continuing')
            for _ in range(2 * 3600):
                Sleep(0.5)
                dataQDeque.load_from_Q(
                    queues['dataQ'], mark_done=True, wait_sec=0.1)
                if _ % 120 == 0:
                    print(f'{str(Dtc.now())} q:{len(dataQDeque)}')

            STOP_EVENTS['acquireData'].set()
            for _ in range(200):
                Sleep(0.001)

            dataQDeque.load_from_Q(  # pick up anything left over.
                queues['dataQ'], mark_done=True, wait_sec=0.1)

            shutdown(futures, queues, STOP_EVENTS)
            break  # break out of tpex
        a = 0
        break  # break out of while loop

    aa: List[Any] = []
    with open('localweathersqlshort.pickle', 'rb') as fl:
        try:
            aa = pickle.load(fl)
        except Exception as ex:
            a = 0

    a = 0

    return


def datagen2(hours: float = 0.5):
    """datagen2(hours=0.5)

    """

    queues = QUEUES
    dq = queues['dataQ']
    timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)

    # turn on selected threads
    bollst: Tuple[bool] = (True, False, False, False, False)
    bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier

    barrier: CTX.Barrier = CTX.Barrier(bc)

    trackerinitialized: float = monotonic()  # returns seconds
    trackerTimeout: float = trackerinitialized + timetup[2]

    trackerstarted = None
    tempdec: Deck = Deck(30)

    while (True):
        futures: Dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
            try:

                futures = {
                    # gets weather data
                    'weather': tpex.submit(timed_work, bollst[0], barrier, STOP_EVENTS['acquireData'], queues, delay=10, timed_func=Get_LW1),
                    # gets banddata data
                    # #'noise': tpex.submit(timed_work, bollst[1], barrier, STOP_EVENTS['acquireData'], 60, Get_NF, queues),
                    # 'noise': tpex.submit(get_noise, bollst[1], barrier, STOP_EVENTS['acquireData'], queues),
                    # reads the dataQ and sends to the data processing queue dpq
                    # fn is wrong
                    # 'transfer': tpex.submit(dataQ_reader_datagen, bollst[2], barrier, STOP_EVENTS['trans'], queues, fn=None),
                    # looks at the data and generates the approprate sql to send to dbwriter
                    # 'dataagragator': tpex.submit(dataaggrator, bollst[3], barrier, STOP_EVENTS['agra'], queues),
                    # reads the database Q and writes it to the database
                    # 'dbwriter': tpex.submit(dbQ_writer, bollst[4], barrier, STOP_EVENTS['dbwrite'], queues),

                }
            except Exception as e:
                aa = 0

            # for _ in range(10):  # let things start and reach the waiting state
                # Sleep(0.001)

            [tempdec.append(f.running()) for f in futures.values()]
            tempdec.loadQ(dq)

            # barrier.wait()  # start them all working
            for _ in range(400):
                Sleep(0.5)
            STOP_EVENTS['acquireData'].set()
            for _ in range(200):
                Sleep(0.001)

            dataQDeque: Deck = Deck(100)
            dataQDeque.load_from_Q(
                queues['dataQ'], mark_done=True, wait_sec=0.1)

            shutdown(futures, queues, STOP_EVENTS)
            break  # break out of tpex
        a = 0
        break  # break out of while loop

    aa: List[Any] = []
    with open('localweathersqlshort.pickle', 'rb') as fl:
        try:
            aa = pickle.load(fl)
        except Exception as ex:
            a = 0

    a = 0

    return


def datagen1(hours: float = 0.5):
    """datagen1(hours=0.5)
    runs the weather task for
    """

    queues = QUEUES
    timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)

    # turn on selected threads
    bollst: Tuple[bool] = (False, False, True, False, False)
    # bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier

    barrier: CTX.Barrier = CTX.Barrier(bc)

    trackerinitialized: float = monotonic()  # returns seconds
    trackerTimeout: float = trackerinitialized + timetup[2]

    trackerstarted = None
    tempdec: Deck = Deck(30)

    while (True):
        futures: Dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            futures = {
                # gets weather data
                'weather': tpex.submit(timed_work, bollst[0], barrier, STOP_EVENTS['acquireData'], queues, delay=60 * 10.5, timed_func=Get_LW),
                # gets banddata data
                # #'noise': tpex.submit(timed_work, bollst[1], barrier, STOP_EVENTS['acquireData'], 60, Get_NF, queues),
                # 'noise': tpex.submit(get_noise, bollst[1], barrier, STOP_EVENTS['acquireData'], queues),
                # reads the dataQ and sends to the data processing queue dpq
                # fn is wrong
                'transfer': tpex.submit(dataQ_reader_datagen, bollst[2], barrier, STOP_EVENTS['trans'], queues, fn=None),
                # looks at the data and generates the approprate sql to send to dbwriter
                # 'dataagragator': tpex.submit(dataaggrator, bollst[3], barrier, STOP_EVENTS['agra'], queues),
                # reads the database Q and writes it to the database
                # 'dbwriter': tpex.submit(dbQ_writer, bollst[4], barrier, STOP_EVENTS['dbwrite'], queues),

            }

            # for _ in range(10):  # let things start and reach the waiting state
            # Sleep(0.001)

            [tempdec.append(f.running()) for f in futures.values()]
            tempdec.loadQ(dq)

            # barrier.wait()  # start them all working
            trackerstarted: float = monotonic()
            trackerschedend: float = trackerstarted + timetup[2]
            #monotonic() < trackerschedend
            # dataQ_reader_datagen will end when done
            tfut = futures['transfer']
            while monotonic() < trackerTimeout:
                Sleep(10)
                if tfut.done():
                    break
            shutdown(futures, queues, STOP_EVENTS)
            break  # break out of tpex
        a = 0
        break  # break out of while loop

    aa: List[Any] = []
    with open('localweathersqlshort.pickle', 'rb') as fl:
        try:
            aa = pickle.load(fl)
        except Exception as ex:
            a = 0

    a = 0

    return


if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
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
    THE_LOGGER.info('trackermain executed as main')
    # LOGGER.setLevel(logging.DEBUG)
    _aa = Dtc.now(timezone.utc)
    if 'datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)' != repr(Dtc.fromtimestamp(0, timezone.utc)):
        print(str(Dtc.now(timezone.utc)))
        raise SystemError(
            'Wrong epic starting date/time, must be Jan 1, 1970 midnight utc')

    try:
        val = 1
        if val == 0:
            main()
        elif val == 1:
            datagen1()
        elif val == 2:
            datagen2()
        elif val == 3:
            datagen3()
        else:
            raise Exception("wrong val")

    except(Exception, KeyboardInterrupt) as exc:
        print(exc)
        sys.exit(str(exc))
    except SystemError as se:
        print(se)
        sys.exit(str(se))

    finally:
        sys.exit('normal exit')
