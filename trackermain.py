#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os
import concurrent.futures

from queue import Empty as QEmpty, Full as QFull

import logging
import logging.handlers
import multiprocessing as mp

import time
import datetime
from collections import deque
from localweather import LocalWeather
import threading
import userinput
import flex
from flex import Flex
from noisefloor import Noisefloor


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/trackermain'

EXITING = False

CTX = mp.get_context('spawn')
QUEUES = {
    'dataQ': CTX.JoinableQueue(maxsize=100),
    'dbQ': CTX.JoinableQueue(maxsize=100),
    'dpQ': CTX.JoinableQueue(maxsize=100)
}


def RESET_QS():
    for _ in QUEUES.values():
        try:
            while True:
                _.get_nowait()
        except QEmpty:
            continue


class Consolidate:
    def __init__(self):
        pass

    def __str__(self):
        return 'no str yet'

    def __repr__(self):
        return 'no repr yet'

    def doit(self, datalst):
        pass


class Aggratator:
    def __init__(self, execute, barrier, stop_event, queues):
        self.dpQ_IN = queues['dpQ']
        self.dbQ_OUT = queues['dbQ']
        self.execute = execute
        self.barrier = barrier
        self.stop_event = stop_event
        #self.dpQ_IN = dpQ_IN
        #self.dbQ_OUT = dbQ_OUT
        self.consolidate = Consolidate()

    def run(self):
        if not self.execute:
            return

        indata = deque([])
        self.barrier.wait()

        print ('Aggratator started')

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
                    time.sleep(10)

            if self.stop_event.is_set():
                break
        print('dataQ_reader ended')


def dataaggrator(execute, barrier, stop_event, queues, debugfn=None):
    if debugfn:
        debugfn(execute, barrier, stop_event, queues)

    else:
        ag = Aggratator(execute, barrier, stop_event, queues)
        ag.run()


def Get_LW(rawDataQ_OUT):
    _lw = LocalWeather()
    _lw.load()
    rawDataQ_OUT.put(_lw)


def Get_NF(rawDataQ_OUT):
    UI = userinput.UserInput()
    NOISE = None
    try:
        UI.request()
        UI.open()
        print("Requested Port can be opened")
        FLEX = Flex(UI)
        NOISE = Noisefloor(FLEX)
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


# rawDataQ_IN, dpQ_OUT):
def dataQ_reader(execute, barrier, stop_event, queues):
    if execute:
        locald = threading.local()
        rawDataQ_IN = queues['dataQ']
        dpQ_OUT = queues['dpQ']
        locald.count = 0
        barrier.wait()
        print('dataQ_reader started\n', end="")
        locald.indata = deque([])

        while True:
            stop_event.wait(10)

            while True:
                try:  # empty rawDataW into indata
                    # add data to the right of the queue
                    locald.indata.append(rawDataQ_IN.get(True, 10))
                except QEmpty:
                    break

                finally:  # now write the locald.indata to the output q
                    pendingwrite = None
                    while True:
                        try:
                            while True:
                                pendingwrite = locald.indata.popleft()
                                dpQ_OUT.put(pendingwrite)
                                rawDataQ_IN.task_done()
                                locald.count += 1

                        except IndexError:  # indata is now empty
                            break

                        except QFull:
                            # put pending data on the left of the queue
                            locald.indata.appendleft(pendingwrite)
                            time.sleep(10)

            if stop_event.is_set() and rawDataQ_IN.empty():
                if not rawDataQ_IN.empty():
                    continue
                break
        print('dataQ_reader ended\n', end="")
        return locald.count


def writesql():
    pass


def dbQ_writer(execute, barrier, stop_event, queues, debugwriter=None):
    """dbQ_writer(barrier, stop_event, dbQIN)

    barrier is a Barrier to make sure everything is ready at the same time
    stop_event is set if we are in the process of shutting down
    dbQin contains sql statments to be passed to the MariaDb engine

    """
    if execute:
        doit = writesql
        if debugwriter:
            doit = debugwriter

        dbQIN = queues['dbQ']
        print('dbQ_writer waiting\n', end='')
        barrier.wait()
        print('dbQ_writer started\n', end='')

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


def timed_work(execute, barrier, stop_event, delayseconds, fu, queues):
    """timed_work(execute, barrier, stop_event, delayseconds, fu, queues)

    execute is a boolean that if True will actually execute fu
    barrier is used to coordinate starting the tasks/threads
    stop_event if set causes the task/thread to stop
    delayseconds is the number of seconds between calls to fu
    fu is the function that will be called on the time basis
    queues is the queue dict, but timed_work only uses 'dataQ' from the dict

    """

    class Sequencer:
        def __init__(self, delayseconds):
            self.delayseconds = delayseconds
            nowis = time.monotonic()
            self.timedeque = deque(
                [nowis + t * delayseconds for t in range(20)])

        def do_it_now(self):
            if self.timedeque[0] > time.monotonic():
                return False

            while self.timedeque[0] < time.monotonic():
                self.timedeque.popleft()
                self.timedeque.append(self.timedeque[-1] + delayseconds)

            return True

    if execute:
        locald = threading.local()
        locald.execute = execute
        raw_data_Q = queues['dataQ']
        locald.stop_event = stop_event
        locald.delayseconds = delayseconds
        locald.fu = fu

        locald.last10executtimes = deque([], 10)  # queue of max length 10
        # print('timed_work waiting to pass barrier\n',end="")
        barrier.wait()
        # print(f'timed_work started: {time.monotonic()}\n',end="")

        locald.seq = Sequencer(delayseconds)
        while not locald.stop_event.wait(1):
            if locald.seq.do_it_now():
                locald.last10executtimes.append(f'{str(datetime.datetime.now().time())}, {str(locald.fu)}')
                # print(datetime.datetime.now().time())
                locald.fu(raw_data_Q)
                time.sleep(0.00001)

            if locald.stop_event.is_set():
                break
        # print(f'timed_work ended: {time.monotonic()}\n',end="")
        return(locald.last10executtimes)


def shutdown(futures, queues, stopevents):
    # stop the data generating processes
    stopevents['acquireData'].set()
    stopevents['trans'].set()
    time.sleep(0.001)
    validkeys = list(futures.keys())

    isdone = True
    # keys are the dict keys for data generation threads
    # selected from weather noise transfer dataagragator dbwriter
    keys = [k for k in validkeys if k in ('weather', 'noise',)]

    while True:
        time.sleep(0.001)
        bb = [futures[k].done() for k in keys]

        cc = [v for v in bb if v]
        if len(cc) == len(bb):
            break

    # wait until the dataQ fileed by the data generating processes empty
    while not queues['dataQ'].empty():
        time.sleep(0.001)

    # the dataQ is empty now ok to stop the datareader
    stopevents['trans'].set()
    if 'transfer' in validkeys:
        while not futures['transfer'].done():
            time.sleep(0.001)

    # stop the data aggragator
    stopevents['agra'].set()
    if 'dataagragator' in validkeys:
        while not futures['dataagragator'].done():
            time.sleep(0.001)

    while not queues['dpQ'].empty():
        time.sleep(0.001)
    # stop the data base writer
    stopevents['dbwrite'].set()
    if 'dbwriter' in validkeys:
        while not futures['dbwriter'].done():
            time.sleep(0.001)


def main(ctx, hours=0.5):

    stopevents = {
        'acquireData': ctx.Event(),
        'trans': ctx.Event(),
        'dbwrite': ctx.Event(),
        'agra': ctx.Event(),
    }
    queues = QUEUES
    # need to log starting
    # setup thread processor
    timetup = (hours, 60 * hours, 3600 * hours,)
    #runtimehours = hours
    #runtimemin = 60 * runtimehours
    #runtimesec = 60 * runtimemin
    bollst = [True, True, True, True, True]
    bc = sum([1 for _ in bollst if _]) + 1

    barrier = ctx.Barrier(bc)

    trackerinitialized = time.monotonic()
    trackerTimeout = trackerinitialized + timetup

    trackerstarted = None
    while (True):
        futures = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:

            futures = {
                # gets weather data
                'weather': tpex.submit(timed_work, bollst[0], barrier, stopevents['acquireData'], 60 * 10.5, Get_LW, queues),
                # gets banddata data
                'noise': tpex.submit(timed_work, bollst[1], barrier, stopevents['acquireData'], 60 * 10.5, Get_NF, queues),
                # reads the dataQ and sends to the data processing queue dpq
                'transfer': tpex.submit(dataQ_reader, bollst[2], barrier, stopevents['trans'], ),
                # looks at the data and generates the approprate sql to send to dbwriter
                'dataagragator': tpex.submit(dataaggrator, bollst[3], barrier, stopevents['agra'], queues),
                # reads the database Q and writes it to the database
                'dbwriter': tpex.submit(dbQ_writer, bollst[4], barrier, stopevents['dbwrite'], queues),

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
            #trackerstarted = time.monotonic()
            #trackerschedend = trackerstarted + runtimesec
            #time.monotonic() < trackerschedend
            # while time.monotonic() < trackerTimeout:
            # time.sleep(5)
            shutdown(futures, queues, stopevents)
            # break  # breack out of ppex
            barrier.wait()  # start them all working
            trackerstarted = time.monotonic()
            trackerschedend = trackerstarted + runtimesec
            time.monotonic() < trackerschedend
            while time.monotonic() < trackerTimeout:
                time.sleep(5)
            shutdown(futures, queues, stopevents)
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

    ctx = mp.get_context('spawn')

    try:
        main(ctx)

    except(Exception, KeyboardInterrupt) as exc:
        print(exc)
        sys.exit(str(exc))

    finally:
        sys.exit('normal exit')
