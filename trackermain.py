#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os
import concurrent.futures
from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set

from queue import Empty as QEmpty, Full as QFull

import multiprocessing as mp
from queuesandevents import CTX, QUEUES, STOP_EVENTS
import logging
import logging.handlers


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
#from noisefloor import Noisefloor
#from qdatainfo import DataQ, DbQ, DpQ, LWQ


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/trackermain'

EXITING = False

# CTX = mp.get_context('spawn')  # threading context

# QUEUES = {
# from data acquisition threads, received by the aggragator thread
# 'dataQ': CTX.JoinableQueue(maxsize=100),
# database commands generateed (usually) ty the aggrator thread
# 'dbQ': CTX.JoinableQueue(maxsize=100),
# written to by the aggrator thread, read by the data processor which generates sql commands to dbq
# 'dpQ': CTX.JoinableQueue(maxsize=100)
# }

# STOP_EVENTS = {
# 'acquireData': CTX.Event(),
# 'trans': CTX.Event(),
# 'dbwrite': CTX.Event(),
# 'agra': CTX.Event(),
# }


# def RESET_QS():
# """RESET_QS()

# empties all the queues, marks task_done as each is removed.
# """
# for _ in QUEUES.values():
# try:
# while True:
# _.get_nowait()
# _.task_done()
# except QEmpty:
# continue


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
        self.barrier.wait()

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
        self.barrier.wait()

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


def Get_LW(rawDataQ_OUT):
    """Get_LW(rawDataQ_OUT)

    Gets Local Medfrod weather in a LocalWeather object and adds it to the rawDataQ_OUT queue.

    """
    from qdatainfo import LWQ
    _lw = LocalWeather()
    _lw.load()
    content: str = _lw.gen_sql()
    pkg: LWQ = LWQ(content)
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


def get_noise():
    if thread_info[0]:  # execute:

        print('get_noise started\n', end="")
        pass
    print('get_noise ended\n', end="")
    return locald.count

# write_2_q):


def dataQ_reader(thread_info, fn=lambda outQ, data: outQ.put(data, False)):
    """dataQ_reader(thread_info)

    this is the 'transfer' thread in futures

     thread_info is (execute, barrier, stop_event, queues,),
     fn is the function to be applied to the input data and defaults to writing data
     to the outQ

    """
    if thread_info[0]:  # execute:
        locald = threading.local()

        rawDataQ_IN = thread_info[3]['dataQ']
        dpQ_OUT = thread_info[3]['dpQ']
        stop_event = thread_info[2]
        locald.count = 0
        thread_info[1].wait()
        print('dataQ_reader started\n', end="")
        # the deque, max size, single element  size inititally 0
        # locald.deqPrams = (Deck(50), 50, [0])
        indeck = Deck(100)
        wetherdec = Deck(100)
        noisedeck = Deck(100)
        lastweather = None
        lastnoise = None

        while True:

            try:  # empty rawDataW into indata
                indeck.load_from_Q(rawDataQ_IN, mark_done=False)

            except QFull:
                pass

            finally:
                if len(indeck) > 0:

                    wetherdec.clear()
                    wetherdec.push(lastweather)
                    noisedeck.clear()
                    noisedeck.push(lastnoise)
                    # separate the indeck contents
                    try:
                        while(len(indeck) > 0):
                            cnt = indeck.popleft()
                            if isinstance(cnt, LocalWeather):
                                wetherdec.append(cnt)
                            elif isinstance(cnt, NFResult):
                                noisedeck.append(cnt)
                            else:
                                raise AssertionError("need to handle")
                    except IndexError:
                        pass
                    finally:
                        pass
                    data_tobe_processed = None
                    tuplst = trim_dups(wetherdec, localweather.different)

                    noiselist = list(noisedeck)
                    noisemarkers = [i for i in range(1, len(weatherlist)) if
                                    (weatherlist[i - 1].has_changedweatherlist[i])]

                    # first item of wetherdec and noisedeck may be None!
                while True:
                    try:
                        while True:
                            # data_tobe_processed = locald.deqPrams[0] \
                                # .popleft()
                            data_tobe_processed = indeck.popleft(
                            )
                            # process the data
                            fn(dpQ_OUT, data_tobe_processed)
                            locald.deqPrams[2][0] = locald.deqPrams[2][0] - 1
                            rawDataQ_IN.task_done()
                            locald.count += 1

                    except QFull:
                        # put pending data on the left of the queue
                        # locald.deqPrams[0].appendleft(data_tobe_processed)
                        locald.deqPrams[0].push(data_tobe_processed)
                        Sleep(10)

                    except IndexError:  # indata is now empty
                        break
            # things look done
            if stop_event.wait(5.0):
                if rawDataQ_IN.empty() and len(locald.deqPrams[0]) == 0:
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
def timed_work(thread_info, delayseconds, fu):
    """timed_work(thread_info, delayseconds, fu, )

    thread_info is (execute, barrier, stop_event, queues,),

    execute is a boolean that if True will actually execute fu
    barrier is used to coordinate starting the tasks/threads
    stop_event if set causes the task/thread to stop
    delayseconds is the number of seconds between calls to fu
    fu is the function that will be called on the time basis
    queues is the queue dict, but timed_work only uses 'dataQ' from the dict

    this is used for the weather and noise threads

    """

    class Sequencer:
        """Sequencer(delayseconds)

        """

        def __init__(self, delayseconds):
            self.delayseconds = delayseconds
            nowis = monotonic()
            self.to_do_sched = deque(
                [nowis + t * delayseconds for t in range(20)])

        def do_it_now(self):
            """ do_it_now()

            Defines if it is time to do something on a todo schedule
            """
            if self.to_do_sched[0] > monotonic():
                return False

            while self.to_do_sched[0] < monotonic():
                self.to_do_sched.popleft()
                self.to_do_sched.append(self.to_do_sched[-1] + delayseconds)

            return True

    if thread_info[0]:
        locald = threading.local()
        locald.execute = thread_info[0]
        raw_data_Q = thread_info[3]['dataQ']
        locald.stop_event = thread_info[2]
        locald.delayseconds = delayseconds
        locald.fu = fu

        locald.last10executtimes = deque([], 10)  # queue of max length 10
        # print('timed_work waiting to pass barrier\n',end="")
        thread_info[1].wait()
        # print(f'timed_work started: {monotonic()}\n',end="")

        locald.seq = Sequencer(delayseconds)
        while not locald.stop_event.wait(1):
            if locald.seq.do_it_now():
                locald.last10executtimes.append(f'{str(Dtc.now().time())}, {str(locald.fu)}')
                # print(datetime.datetime.now().time())
                locald.fu(raw_data_Q)
                Sleep(0.00001)

            if locald.stop_event.is_set():
                break
        # print(f'timed_work ended: {time.monotonic()}\n',end="")
        return(locald.last10executtimes)


def shutdown(futures, queues, stopevents):
    """shutdown(futures, queues, stopevents)

    """
    # stop the data generating processes
    stopevents['acquireData'].set()
    stopevents['trans'].set()
    Sleep(0.001)
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
    """main(ctx, hours=0.5)

    """

    queues = QUEUES
    # need to log starting
    # setup thread processor
    # (hours, min, seconds)
    timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)
    runtimehours: float = float(hours)
    runtimemin: float = 60 * runtimehours
    runtimesec: float = 60 * runtimemin

    # turn on all the threads
    bollst: List[bool] = [True, True, True, True, True]
    bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier

    barrier: CTX.Barrier = CTX.Barrier(bc)

    trackerinitialized: float = monotonic()  # returns seconds
    trackerTimeout: float = trackerinitialized + timetup[2]

    trackerstarted = None
    while (True):
        futures: Dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            futures = {
                # gets weather data
                'weather': tpex.submit(timed_work, bollst[0], barrier, STOP_EVENTS['acquireData'], 60 * 10.5, Get_LW, queues),
                # gets banddata data
                # 'noise': tpex.submit(timed_work, bollst[1], barrier, STOP_EVENTS['acquireData'], 60, Get_NF, queues),
                'noise': tpex.submit(get_noise, bollst[1], barrier, STOP_EVENTS['acquireData'], queues),
                # reads the dataQ and sends to the data processing queue dpq
                'transfer': tpex.submit(dataQ_reader, bollst[2], barrier, STOP_EVENTS['trans'], queues),
                # looks at the data and generates the approprate sql to send to dbwriter
                'dataagragator': tpex.submit(dataaggrator, bollst[3], barrier, STOP_EVENTS['agra'], queues),
                # reads the database Q and writes it to the database
                'dbwriter': tpex.submit(dbQ_writer, bollst[4], barrier, STOP_EVENTS['dbwrite'], queues),

            }

# setup multiprocessor

# with concurrent.futures.ProcessPoolExecutor(max_workers=2) as ppex:
# reads all the data received in the data processing Q organizes it and sends the results to be written
# futures['dataagragator'] = ppex.submit(
# dataaggrator, bollst[3], barrier, stopevents['agra'], queues)
# reads the database Q and writes it to the database
# futures['dbwriter'] = tpex.submit(
# dbQ_writer, bollst[4], barrier, stopevents['dbwrite'], queues)

# barrier.wait()  # start them all working
# trackerstarted = time.monotonic()
# trackerschedend = trackerstarted + runtimesec
# time.monotonic() < trackerschedend
# while time.monotonic() < trackerTimeout:
# Sleep(5)
            shutdown(futures, queues, STOP_EVENTS)
            #                                               break  # breack out of ppex
            barrier.wait()  # start them all working
            trackerstarted: float = monotonic()
            trackerschedend: float = trackerstarted + runtimesec
            monotonic() < trackerschedend
            while monotonic() < trackerTimeout:
                Sleep(5)
            shutdown(futures, queues, STOP_EVENTS)
            break  # break out of tpex
        a = 0
        break  # break out of while loop
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
    if 'time.struct_time(tm_year=1970, tm_mon=1, tm_mday=1, tm_hour=0, tm_min=0, tm_sec=0, tm_wday=3, tm_yday=1, tm_isdst=0)' != str(Dtc.now(timezone.utc)):
        print(str(Dtc.now(timezone.utc)))
        raise SystemError(
            'Wrong epic starting date/time, must be Jan 1, 1970 midnight utc')

    try:
        main()

    except(Exception, KeyboardInterrupt) as exc:
        print(exc)
        sys.exit(str(exc))
    except SystemError as se:
        print(se)
        sys.exit(str(se))

    finally:
        sys.exit('normal exit')
