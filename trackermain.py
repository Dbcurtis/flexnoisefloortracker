#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os


# from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque
from typing import Any, Tuple, List, Dict, Set, Callable

from queue import Empty as QEmpty, Full as QFull
import concurrent.futures
from concurrent.futures import ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED
# import multiprocessing as mp

import logging
import logging.handlers
import pickle
from time import sleep as Sleep
from time import monotonic
from datetime import datetime as Dtc
from datetime import timezone
from collections import deque, namedtuple
import threading


from queuesandevents import CTX, QUEUES, STOP_EVENTS
from queuesandevents import POSSIBLE_F_TKEYS as FK
from queuesandevents import STOP_EVENT_KEYS as SEK
from queuesandevents import QUEUE_KEYS as QK
from queuesandevents import Enables as ENABLES
from queuesandevents import ARG_KEYS as AK

from nfexceptions import StopEventException
from sequencer import Sequencer
from deck import DeckFullError, OutQFullError
from deck import Deck
from localweather import LocalWeather

from userinput import UserInput
from nfresult import NFResult

from flex import Flex
# from noisefloor import Noisefloor
# from qdatainfo import DataQ, DbQ, DpQ, LWQ


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/trackermain'

EXITING = False


TML = threading.local()
TL = TML

Threadargs = namedtuple('Threadargs', ['execute', 'barrier', 'stope',
                                       'qs', 'name', 'interval', 'doit'])


class Consolidate:
    def __init__(self):
        pass

    def __str__(self):
        return 'no str yet'

    def __repr__(self):
        return 'no repr yet'

    def doit(self, datalst):
        pass


def _myprint(a):
    # print(a)
    pass


def _breakwait(barrier):
    barrier.wait()


def _thread_template(arg: Threadargs, printfun=_myprint, **kwargs) -> List[int]:
    """_thread_template(arg, printfun=_myprint, **kwargs)

    Most of the test thread proxies use this
    arg is a Threadargs
    shows that the proxie has been invoked or not, and ended.

    If the proxie is enabled, shows that, waits for the barrier, and then executes doit
    repeatedly at interval timeing, until the stop_event is set


    If the interval timeing is 0 or None, doit gets called once and exits when the stop event is set
    and is responsible for any clean up (like waiting for queues to empty if needed)

    """

    # multiple threads call this, so make the thread variables

    TL.ttarg: Threadargs = arg
    TL.returnval = None

    TL.results: List[Any] = []
    try:
        printfun(
            f'{TL.ttarg.name} invoked, th={threading.current_thread().getName()}, t={monotonic()}')

        if TL.ttarg.execute:  # if the module execution is enabled
            TL.returnval = True

            printfun(f'{TL.ttarg.name} execution enabled waiting')
            TL.ttarg.barrier.wait()
            printfun(
                f'{TL.ttarg.name} starting, th={threading.current_thread().getName()}, t={monotonic()}')
            if TL.ttarg.interval is None:
                doit_result = TL.ttarg.doit()
                return
            elif TL.ttarg.interval == 0:
                doit_result = TL.ttarg.doit()
                TL.results.append(doit_result)
                return

            #
            # the real stuff happens here
            #
            while True:  # doing intervals
                if TL.ttarg.stope.is_set():  # need to clean up

                    return
                else:  # normal operation
                    doitresult = TL.ttarg.doit()  # call it get the return

                    TL.results.append(doitresult)
                    Sleep(TL.ttarg.interval)    # and wait

            # if TL.ttarg.stope.is_set():
                ##notempty = True
                # while notempty:  # repeats calls to doit() until nothing is returned
                    # doit can run for a long time, if doit retuns None or 0, doit is done
                    ##temp: int = TL.ttarg.doit()
                    # if temp is None:
                    # return
                    # if temp is not none, addeded to the results and called again.
                    # TL.results.append(temp)
                    ##notempty = temp != 0

                # return  # will invoke finally
            # else:
                # while not TL.ttarg.stope.is_set():

                    # may need to handle the results
                    # try:
                    # TL.results.append(TL.ttarg.doit())
                    # Sleep(TL.ttarg.interval)
                    # except QFull as qf:
                    # pass

                # Sleep(TL.ttarg.interval)

        else:
            printfun(f'{TL.ttarg.name} execution disabled')
    except Exception as ex:
        print(f'{ex}, on {TL.ttarg.name}')
        raise ex

    finally:
        # and show the module is ending
        _ss = f'{TL.ttarg.name} end, th={threading.current_thread().getName()}, t={monotonic()}'
        printfun(_ss)
        return TL.results


class DBwriter:
    """DBwriter(thread_info)

    thread_info = (execute, barrier, stop_event, queues)
    """

    def __init__(self, thread_info):
        self.dpQ_IN: CTX.JoinableQueue = thread_info[3][QK.dbQ]
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

        print('DBwriter started')

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
    """Aggratator(arg:Threadargs, aggfn=jjj))

    thread_info = (execute, barrier, stop_event, queues)
    """

    def __init__(self, arg: Threadargs, aggfn=jjj):
        self.arg = arg
        self.dpQ_IN: CTX.JoinableQueue = arg.qs[QK.dpQ]
        self.dbQ_OUT: CTX.JoinableQueue = arg.qs[QK.dbQ]

        self.stop_event: CTX.Event = thread_info[2]
        self.consolidate = Consolidate()
        self.fn = aggfn

    def run(self):
        """run()

        """
        if not self.arg.execute:
            return 0
        count = [0]
        # self.barrier.wait()

        print('Aggratator started')

        deck = Deck(50)
        while True:
            # while not self.arg.stope.wait(10):
            while True:
                try:
                    deck.q2deck(self.dpQ_IN, True)

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


def dataaggrator_dbg(arg: Threadargs, **kwargs) -> List[Tuple[int, int]]:
    """dataaggrator_dbg

    just passes the entries on the dpQ on to the dbQ
    """
    mma: Threadargs = None
    deck: Deck = Deck(200)

    def doita() -> Tuple[int, int]:

        count: Tuple[int, int] = _qcpy(
            deck, mma.qs[QK.dpQ], mma.qs[QK.dbQ], mma)
        return count

    mma = arg._replace(
        name='dataaggrator_dbg', doit=doita)
    return _thread_template(mma, **kwargs)


# def dataaggrator(thread_info, aggfn=None, debugfn=None):
def dataaggrator(arg: Threadargs, aggfn=None, debugfn=None, **kwargs):
    """dataaggrator(thread_info, debugfn=None)

    this is the 'dataagragator' thread in futures

     thread_info is (execute, barrier, stop_event, queues,),
     >>>>>>>>>>>>>>>>name should be dta_agg

    """
    if debugfn:
        return debugfn(arg)

    else:
        ag = Aggratator(arg, aggfn)
        return ag.run()


def genargs(barrier: CTX.Barrier, bollst: Tuple[bool, ...]) -> Dict[int, Threadargs]:
    """genargs(barrier,bollst)
    returns a dict of str and Threadards

    the Threadargs are used to feed the threads,
    They can be modified after being generated

    """
    result: Dict(int, Threadargs) = {}
    result[AK.w] = Threadargs(
        bollst.w, barrier, STOP_EVENTS[SEK.ad], QUEUES, name='timed_work', interval=None, doit=None)

    result[AK.n] = Threadargs(
        bollst.n, barrier, STOP_EVENTS[SEK.ad], QUEUES, name='nf', interval=None, doit=None)

    result[AK.t] = Threadargs(
        bollst.t, barrier, STOP_EVENTS[SEK.t], QUEUES, name='dqr', interval=None, doit=None)

    result[AK.da] = Threadargs(
        bollst.da, barrier, STOP_EVENTS[SEK.da], QUEUES, name='da', interval=None, doit=None)

    result[AK.db] = Threadargs(
        bollst.db, barrier, STOP_EVENTS[SEK.db], QUEUES, name='db', interval=None, doit=None)

    #result[AK.w] = twargs
    #result[AK.n] = nfargs
    #result[AK.t] = dqrargs
    #result[AK.da] = daargs
    #result[AK.db] = dbargs

    return result


def Get_LW_dbg(arg: Threadargs, **kwargs):
    #arg: Threadargs = argin.replace(name='Get_LW_dbg')
    que = arg.qs[QK.dQ]
    data = f'{arg.name + "_Get_LW_dbg"} th={threading.current_thread().getName()}, t={monotonic()}'
    que.put_nowait(data)


def Get_LW(arg: Threadargs, **kwargs):
    """Get_LW(arg: Threadargs, **kwargs)

    Runs on a timed_work thread
    Gets Local Medfrod weather in a LocalWeather object and adds it to the rawDataQ_OUT queue.

    """
    from qdatainfo import LWQ
    _lw = LocalWeather()
    _lw.load()
    parital_sql: str = _lw.gen_sql()
    pkg: LWQ = LWQ(parital_sql)
    try:
        arg.qs[QK.dQ].put(pkg)
    except QFull:
        print("dataq full for local weather--- skipped")
        raise

    # rawDataQ_OUT.put(_lw)


# def Get_NF(rawDataQ_OUT):
    # """Get_NF(rawDataQ_OUT)

    # this thread function is the only one that starts and uses the Flex

    # >>>>>>>>>>>>>>>>name should be get_nf

    # """
    #from noisefloor import Noisefloor
    #_ui: UserInput = UserInput()
    #_noisf = None
    # try:
        # _ui.request(port='com4')
        # _ui.open()
        #print("Requested Port can be opened")
        #FLEX = Flex(_ui)
        #_noisf = Noisefloor(FLEX, rawDataQ_OUT)
        # _noisf.open()
        # 10 loops with a 30 second delay between each
        #_noisf.doit(loops=10, interval=30)
        # _noisf.close()

    # except(Exception, KeyboardInterrupt) as exc:
        # if _noisf:
        # _noisf.close()
        # _ui.close()
        # sys.exit(str(exc))

    # finally:
        # if _noisf:
        # _noisf.close()
        # _ui.close()
        # sys.exit(str(exc))
    ## _nf = NoiseFloor()


def trim_dups(mydeck, boolfn):
    if not mydeck:
        return []
    lst = list(mydeck)
    tuplst = [(boolfn(lst[i], lst[i + 1]), lst[i], lst[i + 1],)
              for i in range(len(lst) - 1)]
    return tuplst


def get_noise1(arg: Threadargs, **kwargs):
    """get_noise1(arg:Threadargs, **kwargs)
    arg    Threadargs', ['execute', 'barrier', 'stope',
                                       'qs', 'name', 'interval', 'doit'])

    """
    from flex import Flex
    from postproc import BANDS, BandPrams, INITIALZE_FLEX
    from noisefloor import Noisefloor

    def doita():
        initial_state = None
        UI: UserInput = UserInput()
        nf: Noisefloor = None

        try:

            UI.request(port='com4')
            flexr: Flex = Flex(UI)
            initial_state = flexr.save_current_state()
            flexr.do_cmd_list(INITIALZE_FLEX)
            if not flexr.open():
                raise (RuntimeError('Flex not connected to serial serial port'))
            # flex: Flex, out_queue: CTX.JoinableQueue, stop_event: CTX.Event
            nf = Noisefloor(
                flexr, arg.qs[QK.dQ], arg.stope, run_till_stopped=True)
            nf.open()
            nf.doit(loops=0, interval=5 * 60, runtime=0, dups=True)
        except StopEventException as see:
            nf.close()
            raise see

        finally:
            #print('restore flex prior state')
            flexr.restore_state(initial_state)

            if nf:
                nf.close()  # also closes flex and ui
            UI.close()

    mma: Threadargs = arg._replace(name='get_noise1', doit=doita)
    return _thread_template(mma, **kwargs)


def get_noise(arg: Threadargs, **kwargs):
    """get_noise(arg,**kwargs)

    Threadargs', ['execute', 'barrier', 'stope',
                                       'qs', 'name', 'interval', 'doit'])

    A thread function to start the data acquisition thread on the flex.

    """
    from flex import Flex
    from postproc import BANDS, BandPrams, INITIALZE_FLEX
    from noisefloor import Noisefloor

    if arg.execute:  # execute:
        arg.barrier.wait()
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

            nf = Noisefloor(flexr, arg.qs[QK.dQ], arg.stope)
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

        TL.rawDataQ_IN = ti_dict['queues'][QK.dQ]

        TL.count = 0
        # ti_dict['barrier'].wait()  # wait for the barrier
        print('dataQ_reader_datagen started\n', end="")
        # the deque, max size, single element  size inititally 0
        # locald.deqPrams = (Deck(50), 50, [0])
        deck = Deck(100)

        while True:
            try:  # empty rawDataW into indata
                # waits for 10sec to try to empty Q
                deck.q2deck(TL.rawDataQ_IN, mark_done=True)

            except QFull:  # the deck is full
                print(f'indeck is full {len(indeck)}')

            finally:
                if len(deck) >= 20:  # deck is 100 so this should work w/o problems
                    break

        templst: List[Any] = []
        try:
            while True:
                templst.append(deck.popleft())
        except IndexError:
            pass  # indeck now wmpty
        with open('localweathersqlshort.pickle', 'wb') as fl:
            try:
                pickle.dump(templst, fl)
            except Exception as ex:
                a = 0

        print('dataQ_reader_datagen ended\n', end="")
        return TL.count

    pass


def _qcpy(deckin, qin, qout, arg: Threadargs, markdone=True, **kwargs) -> Tuple[int, int]:
    """_qcpy(deckin, qin, qout, arg):

    if markdone is True, then the entries from the joinablequeue are marked done when removed
    from qin and placed in the deck.  If false, these entries are marked done when moved from
    the deck into qout.

    returns a tuple with [0] being the number read from qin, and [1] number copied to the oque
    """

    TL.qcarg = arg
    TL.countin = 0
    TL.countout = 0
    TL.deck = deckin
    TL.markdone = markdone
    TL.qin = qin
    TL.qout = qout

    TL.run = True
    TL.testloop = None
    if kwargs:
        try:
            TL.testloop = int(kwargs['loops'])
        except KeyError:
            pass

    TL.q2deckdone = None
    TL.deck2qdone = None

    if TL.markdone:
        TL.q2deckdone = True
        TL.deck2qdone = None
    else:
        TL.q2deckdone = False
        TL.deck2qdone = qin

    TL.run: bool = True

    while TL.run:
        try:
            TL.countin += TL.deck.q2deck(TL.qin,
                                         mark_done=TL.q2deckdone)
        except DeckFullError as dfe:
            _ = str(dfe).split('=')
            if _[0] == 'cnt':
                TL.countin += int(_[1])

        try:
            TL.countout += TL.deck.deck2q(
                TL.qout, done_Q=TL.deck2qdone)
        except OutQFullError as oqfe:
            _ = str(oqfe).split('=')
            if _[0] == 'cnt':
                TL.countout += int(_[1])
            Sleep(TL.qcarg.interval)

        if TL.qcarg.stope.is_set() and qin.empty() and len(TL.deck) == 0:
            TL.run = False
        elif TL.testloop is not None:
            TL.testloop -= 1
            TL.run = TL.testloop > 0
        if TL.run:
            Sleep(TL.qcarg.interval)

    return (TL.countin, TL.countout,)


def Get_NF_dbg(arg: Threadargs, **kwargs) -> List[int]:
    """Get_NF_dbg

    just generates some entries into the dataQ
    """
    mma: Threadargs = None

    def doita() -> int:
        data: str = f'{mma.name} th={threading.current_thread().getName()}, t={monotonic()}'
        dq = mma.qs[QK.dQ]
        dq.put(data)
        return 1

    mma = arg._replace(doit=doita, name='Get_NF_dbg')
    return _thread_template(mma, **kwargs)


def dataQ_reader_dbg(arg: Threadargs, **kwargs) -> List[Tuple[int, int]]:
    """dataQ_reader_dbg

    just passes the entries on the dataQ on to the dpQ
    """
    deck: Deck = Deck(200)
    mma: Threadargs = None

    def doita() -> Tuple[int, int]:
        """doit()


        """
        count: Tuple[int, int] = _qcpy(
            deck, mma.qs[QK.dQ], mma.qs[QK.dpQ], mma)
        return count

    mma = arg._replace(doit=doita, name='dataQ_reader_dbg')
    return _thread_template(mma, **kwargs)


def dataQ_reader(arg: Threadargs, **kwargs):
    """dataQ_reader(*args, **kwargs)

    this is the 'transfer' thread in futures

     arg is a Threadargs with attributes:
     ['execute', 'barrier', 'stope','qs', 'name', 'interval', 'doit'])
     'fn' in kwargs is the function to be applied to the input data and defaults to writing data
     to the outQ

     >>>>>>> name should be dq_reader
    """
    # ------------------------------------ left in screwy state <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    """
    data processing proxie
    arg is named tuple Threadargs
    """
    deck: Deck = Deck(50)
    mma: Threadargs = None

    def doita():
        # (deckin, qin, qout, args, markdone=True, **kwargs) -> Tuple[int, int]:

        _qcpy(deck, mma.qs[QK.dQ], mma.qs[QK.dpQ], arg)
        return 0

    # update the interval and function

    mma = arg._replace(
        interval=10, doit=doita)
    return _thread_template(mma, **kwargs)  # run it
    # ------------------------
    deck = Deck(50)

    def doita():
        return 0
    if not arg.execute:  # if disabled, just exit to kill the thread
        return

    #
    TL.dqrarg: Threadargs = arg
    TL.fn = None
    try:
        TL.fn = kwargs['fn']
    except KeyError:
        pass

    import localweather

    TL.rawDataQ_IN = TL.dqrarg.qs[QK.dQ]
    TL.dpQ_OUT = TL.dqrarg.qs[QK.dpQ]
    # TL.stop_event = TL.dqrarg.stope
    TL.count = 0
    TL.dqrarg.barrier.wait()
    print('dataQ_reader started\n', end="")
    # the deque, max size, single element  size inititally 0
    TL.deqPrams = (Deck(50), 50, [0])
    TL.indeck = Deck(100)
    TL.wetherdec = Deck(100)
    TL.noisedeck = Deck(100)
    TL.lastweather = None
    TL.lastnoise = None

    while True:
        try:  # empty rawDataW into indata
            TL.indeck.q2deck(
                TL.rawDataQ_IN, mark_done=False)

        except QFull:
            pass

        finally:
            if len(TL.indeck) > 0:

                TL.wetherdec.clear()
                TL.wetherdec.push(TL.lastweather)
                TL.noisedeck.clear()
                TL.noisedeck.push(TL.lastnoise)
                # separate the indeck contents
                try:
                    while(len(TL.indeck) > 0):
                        cnt = TL.indeck.popleft()
                        if isinstance(cnt, LocalWeather):
                            TL.wetherdec.append(cnt)
                        elif isinstance(cnt, NFResult):
                            TL.noisedeck.append(cnt)
                        else:
                            raise AssertionError(
                                "not LocalWeather or NFResult in dataq")
                except IndexError:
                    pass
                finally:
                    pass
                data_tobe_processed = None
                TL.tuplst = trim_dups(
                    TL.wetherdec, localweather.different)

                TL.noiselist = list(TL.noisedeck)
                TL.noisemarkers = [i for i in range(1, len(weatherlist)) if
                                   (weatherlist[i - 1].has_changedweatherlist[i])]

                # first item of wetherdec and noisedeck may be None!
            while True:
                try:
                    while True:
                        # data_tobe_processed = locald.deqPrams[0] \
                        # .popleft()
                        TL.data_tobe_processed = indeck.popleft()
                        # process the data
                        TL.fn(TL.dpQ_OUT, data_tobe_processed)
                        TL.deqPrams[2][0] = TL.deqPrams[2][0] - 1
                        TL.rawDataQ_IN.task_done()
                        TL.count += 1

                except QFull:
                    # put pending data on the left of the queue
                    # locald.deqPrams[0].appendleft(data_tobe_processed)
                    TL.deqPrams[0].push(data_tobe_processed)
                    Sleep(10)

                except IndexError:  # indata is now empty
                    break
        # things look done
        if not TL.dqrarg.stope.wait(5.0):  # check this
            if TL.rawDataQ_IN.empty() and len(TL.deqPrams[0]) == 0:
                break

    print('dataQ_reader ended\n', end="")
    return TL.count


def read_inQ_2deque():
    result = True
    return result


def writesql():
    pass


def dbQ_writer_dbg(arg: Threadargs, **kwargs) -> List[Tuple[int, int]]:
    """dataQ_reader_dbg

    just passes the entries on the dbQ on to the debugResultQ in kwargs.
    """
    debq = kwargs['debugResultQ']
    deck: Deck = Deck(200)
    mma: Threadargs = None

    def doita() -> Tuple[int, int]:

        count: Tuple[int, int] = _qcpy(deck, mma.qs[QK.dbQ], debq, mma)
        return count

    mma = arg._replace(
        name='dbQ_writer_dbg', doit=doita)
    return _thread_template(mma, **kwargs)


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

        dbQIN = thread_info[3][QK.dbQ]
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


def timed_work(arg: Threadargs, **kwargs):  # thread_info, delayseconds, fu):
    """timed_work(arg, **kwargs)

    arg is a Threadargs
    kwargs can be printfn=function used to print, if not set, does not print

    will continue forever until the stop event

    queues is the queue dict, but timed_work only uses 'dataQ' from the dict

    """

    # locald = TML
    TL.twarg: Threadargs = arg
    TL.returnval = None

    def nullprint(arg):
        pass
    TL.myprint = nullprint

    if 'printfn' in kwargs.keys():
        TL.myprint = kwargs['printfn']
    TL.myprint(
        f'{TL.twarg.name} invoked on thread: {threading.current_thread().getName()}')

    if TL.twarg.execute:
        TL.returnval = deque([], 10)  # queue of max length 10

        TL.thread = threading.current_thread()
        TL.tname = TL.thread.getName()
        TL.fu = TL.twarg.doit

        TL.myprint(
            f'{TL.twarg.name} enabled,  waiting to pass barrier')
        TL.twarg.barrier.wait()  # barrier pass
        TL.myprint(f'{TL.twarg.name} started: {monotonic()}')

        TL.seq = Sequencer(TL.twarg.interval)
        # wait to see if the stop event is set
        # while not locald.stop_event.wait(0.45):  # wait is only false if the timeout happens
        while True:
            if TL.twarg.stope.is_set():
                break
            if TL.seq.do_it_now():
                TL.returnval.append(
                    f'{str(Dtc.now().time())}')
                # print(locald.last10executtimes)
                # print('invoke')
                # TL.fu(TL.twarg.qs['dataQ'])
                TL.fu(TL.twarg)
            else:
                _waittime = TL.seq.get_nxt_wait()
                # print(_waittime)
                if _waittime > 1.0:
                    # print('sleep delay')
                    Sleep(1.0)
                elif _waittime <= 0.0009:
                    continue
                else:
                    # the 0.001 should ensure that do_it_now returns true
                    Sleep(_waittime + 0.001)
    else:
        TL.myprint(f'{TL.twarg.name} disabled')

    TL.myprint(f'{TL.twarg.name} end: {monotonic()}')
    return(TL.returnval)


def shutdown(futures: Dict[str, Any], queues, stopevents, time_out=30) -> Tuple[Set, Set]:
    """shutdown(futures, queues, stopevents)
    returns wait results

    """

    # contains the keys for the defined importaint threads

    fkeys_inorder: List[str] = [
        k for k in list(FK) if k in futures.keys() and futures[k]]
    if not fkeys_inorder:
        return None

    class DataaccShutdown:
        def __init__(self):
            self.w_is_shutdown = not FK.w in fkeys_inorder
            self.n_is_shutdown = not FK.n in fkeys_inorder
            self.disabled = self.w_is_shutdown and self.n_is_shutdown  # this object is invalid
            pass

        def w_sd(self):
            self.w_is_shutdown = True
            self.donext()

        def n_sd(self):
            self.n_is_shutdown = True
            self.donext()

        def donext(self):
            if not self.disabled \
               and self.n_is_shutdown \
               and self.w_is_shutdown \
               and SEK.t in fkeys_inorder:
                # just keeping the stop events status consistent
                STOP_EVENTS[SEK.ad].set()
                # print('stop trans')
                STOP_EVENTS[SEK.t].set()

            pass

    acc: DataaccShutdown = DataaccShutdown()

    def weather_shutdown(f):
        acc.w_sd()

    def noise_shutdown(f):
        acc.n_sd()

    def transfer_shutdown(f):
        # print('stop agra')
        # just keeping the stop events status consistent
        STOP_EVENTS[SEK.t].set()
        STOP_EVENTS[SEK.da].set()

    def agra_shutdown(f):
        # print('stop dbwrite')
        # just keeping the stop events status consistent
        STOP_EVENTS[SEK.da].set()
        STOP_EVENTS[SEK.db].set()

    def dbwrite_shutdown(f):
        # just keeping the stop events status consistent
        STOP_EVENTS[SEK.db].set()
        pass

    shutdowns: Dict[str, Callable] = {
        FK.w: weather_shutdown,
        FK.n: noise_shutdown,
        FK.t: transfer_shutdown,
        FK.da: agra_shutdown,
        FK.db: dbwrite_shutdown
    }

    alldone: bool = True
    for _ in futures.values():
        alldone = alldone and _.done()

    if not alldone:
        for k in fkeys_inorder:
            # and futures[k].result is not None):
            if futures[k].running() or (futures[k].done()):
                futures[k].add_done_callback(shutdowns[k])

        stopevents[SEK.ad].set()

    waitresults: Tuple[Set, Set] = None
    for _ in range(time_out):
        waitresults = concurrent.futures.wait(
            futures.values(), timeout=1, return_when=ALL_COMPLETED)
        if len(waitresults.not_done) == 0:
            break

    return waitresults


def main(hours: float = 0.5):
    """main(hours=0.5)

    """
    def breakwait(barrier):
        barrier.wait()
        myprint('breakwait started')

    queues = QUEUES
    timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)

    # enable all the threads
    bollst: List[bool, ...] = ENABLES(
        w=True, n=True, t=True, da=True, db=True)
    bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier

    #barrier: CTX.Barrier = CTX.Barrier(bc)

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
            futures = {}
            twargs: Threadargs = Threadargs(
                bollst[0], barrier, STOP_EVENTS['acquireData'], queues, name='timed_work', interval=60 * 10.5, doit=Get_LW)

            nfargs: Threadargs = Threadargs(
                bollst[1], barrier, STOP_EVENTS['acquireData'], queues, name='nf', interval=None, doit=None)

            dqrargs: Threadargs = Threadargs(
                bollst[2], barrier, STOP_EVENTS['trans'], queues, name='dqr', interval=None, doit=None)

            daargs: Threadargs = Threadargs(
                bollst[3], barrier, STOP_EVENTS['agra'], queues, name='da', interval=None, doit=None)

            dbargs: Threadargs = Threadargs(
                bollst[4], barrier, STOP_EVENTS['dbwrite'], queues, name='db', interval=None, doit=None)

            def bwdone(f):
                print('breakwait done')

            futures[FK.w] = tpex.submit(timed_work, twargs)
            futures[FK.n] = tpex.submit(get_noise1, nfargs)
            futures[FK.t] = tpex.submit(dataQ_reader, dqrargs)
            futures[FK.da] = tpex.submit(dataaggrator, daargs)
            futures[FK.db] = tpex.submit(dbQ_writer, dbargs)

        for _ in range(10):  # let things start and reach the waiting state
            Sleep(0.001)
            # barrier.wait()  # start them all working
            trackerstarted: float = monotonic()
            trackerschedend: float = trackerstarted + timetup[2]
            _ = tpex.submit(breakwait, barrier)
            _.add_done_callback(bwdone)
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
    dq = queues[QK.dQ]
    timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)

    # turn on selected threads
    bollst: Tuple[bool, ...] = ENABLES(
        w=True, n=True, t=True, da=False, db=False)
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
                futures = {}
                twargs: Threadargs = Threadargs(
                    bollst[0], barrier, STOP_EVENTS['acquireData'], queues, name='timed_work', interval=60 * 10.5, doit=Get_LW)

                nfargs: Threadargs = Threadargs(
                    bollst[1], barrier, STOP_EVENTS['acquireData'], queues, name='nf', interval=None, doit=None)

                dqrargs: Threadargs = Threadargs(
                    bollst[2], barrier, STOP_EVENTS['trans'], queues, name='dqr', interval=None, doit=None)

                daargs: Threadargs = Threadargs(
                    bollst[3], barrier, STOP_EVENTS['agra'], queues, name='da', interval=None, doit=None)

                dbargs: Threadargs = Threadargs(
                    bollst[4], barrier, STOP_EVENTS['dbwrite'], queues, name='db', interval=None, doit=None)

                def bwdone(f):
                    print('breakwait done')

                futures[FK.w] = tpex.submit(timed_work, twargs)
                # futures[FK.n] = tpex.submit(get_noise, nfargs)
                # futures[FK.t] = tpex.submit(dataQ_reader, dqrargs)
                # futures[FK.da] = tpex.submit(dataaggrator, daargs)
                # futures[FK.db]= tpex.submit(dbQ_writer, dbargs)

                # futures = {
                # gets weather data
                # 'weather': tpex.submit(timed_work, bollst[0], barrier, STOP_EVENTS['acquireData'], queues, delay=60 * 10.5, timed_func=Get_LW),
                # gets banddata data
                # 'noise': tpex.submit(timed_work, bollst[1], barrier, STOP_EVENTS['acquireData'], 60, Get_NF, queues),
                # 'noise': tpex.submit(get_noise, bollst[1], barrier, STOP_EVENTS['acquireData'], queues),
                # reads the dataQ and sends to the data processing queue dpq
                # fn is wrong
                # 'transfer': tpex.submit(dataQ_reader, bollst[2], barrier, STOP_EVENTS['trans'], queues, fn=None),
                # looks at the data and generates the approprate sql to send to dbwriter
                # 'dataagragator': tpex.submit(dataaggrator, bollst[3], barrier, STOP_EVENTS['agra'], queues),
                # reads the database Q and writes it to the database
                # 'dbwriter': tpex.submit(dbQ_writer, bollst[4], barrier, STOP_EVENTS['dbwrite'], queues),

                # }
            except Exception as e:
                aa = 0

            [tempdec.append(f.running()) for f in futures.values()]
            tempdec.deck2q(dq)
            dataQDeque: Deck = Deck(10000)
            print('main waiting for start')
            for _ in range(200):
                ss = [(k, v) for k, v in futures.items()]
                Sleep(1)

            _ = tpex.submit(breakwait, barrier)
            _.add_done_callback(bwdone)
            print('main continuing')
            for _ in range(2 * 3600):
                Sleep(0.5)
                dataQDeque.q2deck(
                    queues[QK.dQ], mark_done=True, wait_sec=0.1)
                if _ % 120 == 0:
                    print(f'{str(Dtc.now())} q:{len(dataQDeque)}')

            STOP_EVENTS['acquireData'].set()
            for _ in range(200):
                Sleep(0.001)

            dataQDeque.q2deck(  # pick up anything left over.
                queues[QK.dQ], mark_done=True, wait_sec=0.1)

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
    dq = queues[QK.dQ]
    timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)

    # turn on selected threads
    bollst: Tuple[bool, ...] = ENABLES(True, False, False, False, False)
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

                futures = {}
                twargs: Threadargs = Threadargs(
                    bollst.w, barrier, STOP_EVENTS[SEK.ad], queues, name='timed_work', interval=60 * 10.5, doit=Get_LW)

                nfargs: Threadargs = Threadargs(
                    bollst.n, barrier, STOP_EVENTS[SEK.ad], queues, name='nf', interval=None, doit=None)

                dqrargs: Threadargs = Threadargs(
                    bollst.t, barrier, STOP_EVENTS[SEK.t], queues, name='dqr', interval=None, doit=None)

                daargs: Threadargs = Threadargs(
                    bollst.da, barrier, STOP_EVENTS[SEK.da], queues, name='da', interval=None, doit=None)

                dbargs: Threadargs = Threadargs(
                    bollst.db, barrier, STOP_EVENTS[SEK.db], queues, name='db', interval=None, doit=None)

                def bwdone(f):
                    print('breakwait done')

                futures[FK.w] = tpex.submit(timed_work, twargs)
                # futures[FK.n] = tpex.submit(get_noise, nfargs)
                # futures[FK.t] = tpex.submit(dataQ_reader, dqrargs)
                # futures[FK.da] = tpex.submit(dataaggrator, daargs)
                # futures[FK.db] = tpex.submit(dbQ_writer, dbargs)
            except Exception as e:
                aa = 0

            # for _ in range(10):  # let things start and reach the waiting state
                # Sleep(0.001)

            [tempdec.append(f.running()) for f in futures.values()]
            tempdec.deck2q(dq)

            # barrier.wait()  # start them all working
            _ = tpex.submit(breakwait, barrier)
            _.add_done_callback(bwdone)
            for _ in range(400):
                Sleep(0.5)
            STOP_EVENTS[SEK.ad].set()
            for _ in range(200):
                Sleep(0.001)

            dataQDeque: Deck = Deck(100)
            dataQDeque.q2deck(
                queues[QK.dQ], mark_done=True, wait_sec=0.1)

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


def myprint(*arg):
    # print(arg)
    pass


def runthreads(barrier: CTX.Barrier, calls: Tuple[Callable, ...], argdicin: Dict[str, Threadargs], tpex) -> Dict[str, Any]:

    def bwdone(f):
        pass

    def breakwait(barrier):
        barrier.wait()

    futures: Dict[str, Any] = {}
    futures[FK.w] = tpex.submit(
        calls.w, argdicin[AK.w], printfn=myprint) if calls.w else None

    # gets banddata data
    futures[FK.n] = tpex.submit(calls.n, argdicin[AK.n]) if calls.n else None

    # reads the dataQ and sends to the data processing queue dpq
    futures[FK.t] = tpex.submit(calls.t, argdicin[AK.t]) if calls.t else None

    # looks at the data and generates the approprate sql to send to dbwriter
    futures[FK.da] = tpex.submit(
        calls.da, argdicin[AK.da]) if calls.da else None

    # reads the database Q and writes it to the database
    futures[FK.db] = tpex.submit(
        calls.db, argdicin[AK.db]) if calls.db else None

    _ = tpex.submit(breakwait, barrier)  # break the barrier
    _.add_done_callback(bwdone)
    return futures


def datagen1(hours: float = 0.5):
    """datagen1(hours=0.5)
    runs the weather task and the noise task for 30 min capturing filling the dataQ,

    generates a list of the stuff in the queue and pickles it to a file

    """

    #queues = QUEUES
    #timetup: Tuple[float, ...] = (hours, 60 * hours, 3600 * hours,)

    # enable selected threads

    bollst: Tuple[bool, ...] = ENABLES(
        w=True, n=True, t=False, da=False, db=False)
    bc: int = sum([1 for _ in bollst if _]) + 1  # count them for barrier

    barrier = CTX.Barrier(bc)
    calls: Tuple[Callable, ...] = ENABLES(w=timed_work,
                                          n=get_noise1, t=None, da=None, db=None)

    # trackerinitialized: float = monotonic()  # returns seconds
    #trackerTimeout: float = trackerinitialized + timetup[2]

    #trackerstarted = None

    argdic: Dict[int, Threadargs] = genargs(barrier, bollst)
    # mods for test
    argdic[AK.w] = argdic[AK.w]._replace(
        name='timed_work', interval=60 * 5.5, doit=Get_LW)
    argdic[AK.n] = argdic[AK.n]._replace(
        interval=None)
    argdic[AK.t] = argdic[AK.t]._replace(
        interval=1)
    argdic[AK.da] = argdic[AK.da]._replace(
        interval=1)
    argdic[AK.db] = argdic[AK.db]._replace(
        interval=1)

    futures: Dict[str, Any] = {}
    waitresults: Tuple[Set, Set] = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='dbc-') as tpex:
        futures = runthreads(barrier, calls, argdic, tpex)
        for _ in range(60):  # wait for a while to let the threads work
            Sleep(5)
            print('.', end='')
        STOP_EVENTS[SEK.da].set()  # stop the the data acquisition
        waitresults = shutdown(
            futures, QUEUES, STOP_EVENTS, time_out=120)  # wait max 60 for the threads to stop
        aa = 0

    deck = Deck(1000)
    deck.q2deck(QUEUES[QK.dQ], mark_done=True)
    aa: List[Any] = []
    bb: List[Any] = []
    try:
        while True:
            aa.append(deck.popleft())
    except:
        pass

    with open('dadata30min.pickle', 'wb') as fl:
        try:
            pickle.dump(aa, fl)
        except Exception as ex:
            a = 0

    with open('dadata30min.pickle', 'rb') as f2:
        try:
            bb = pickle.load(fl)
        except Exception as ex:
            a = 0

    for a, b in zip(aa, bb):
        if not a == b:
            print(f'a:{a}, b:{b}')
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
