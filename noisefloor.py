#!/usr/bin/env python3

"""noisefloor.py
   This module provides

"""

import sys
import os
from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict
import logging
import logging.handlers
import datetime
import pickle
from time import sleep as Sleep
from time import monotonic
from queue import Empty as QEmpty
import multiprocessing as mp
from queuesandevents import CTX, QUEUES, STOP_EVENTS

from nfresult import NFResult
from userinput import UserInput
from bandreadings import Bandreadings
from flex import Flex
from postproc import BANDS, BandPrams, INITIALZE_FLEX
from qdatainfo import NFQ
#from trackermain import QUEUES, STOP_EVENTS, CTX


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/noiseFloor'

# CTX = mp.get_context('spawn')  # threading context
#print('CTX should not be defined here ******************************')


class Noisefloor:
    """Noisefloor(flex, out_queue, stop_event, testdata=None, )
       testdata is a filename with a pickle extension
    """

    # , testdata=None):
    def __init__(self, flex: Flex, out_queue: CTX.JoinableQueue, stop_event: CTX.Event):
     #   def __init__(self, userI, testdata=None):

        self.flex: Flex = flex
        self._ui: UserInput = flex._ui
        self.out_queue: CTX.JoinableQueue = out_queue
        self.stop_event: CTX.Event = stop_event
        self._last_band_readings: NFResult = None

        self.end_time = None
        self.initial_state = None
        self.is_open = False

    def __str__(self):
        return '[ {}, {}]'.format('junk0', 'junk1')

    def __repr__(self):
        return '[Noisefloor: {}, {}]'.format('junk0', 'junk1')

    def open(self, detect_br=False) -> bool:
        """open( detect_br)

        Configures and opens the serial port and flex if able,

        saves the current state of the flex in initial_state

         if noisefloor is already open, returns False

        If the serial port is opened and if detect_br: the baud rate of the controller is
        found and the serial port so set.

        If detect_br is True, the baud rate will be detected by establishing
        communication with the controller

        """
        if (self.is_open):
            return False
        try:

            self._ui.open(detect_br)
            self.flex.open(detect_br)
            self.initial_state = self.flex.save_current_state()
            self.is_open = True

        except Exception as sex:
            if self.initial_state:
                self.flex.restore_state(self.initial_state)
            self._ui.comm_port = ""
            print(sex)
            self.is_open = False

        return self.is_open

    def close(self) -> bool:
        """close()
        closes Noisefloor
        return False if Noisefloor is not open
        resets flex to state it was in when opened.
        """
        if not self.is_open:
            return False

        if self.initial_state:
            self.flex.restore_state(self.initial_state)
        self.flex.close()
        self.is_open = False
        # self.dbase.close()
        return True

    # noisefloordata: Sequence[Bandreadings]):
    def _recordprocdata(self, nfr: NFResult):
        """_recordprocdata()

        Sends the band data to the data queue in a NFQ wrapper
        """
        # for br in noisefloordata:
        # br.flexradio = None
        print('- ', end='')
        _nfq = NFQ(nfr)
        self.out_queue.put(_nfq)
        # print (f'queued {noisefloordata}')

    def _oneloopallbands(self) -> NFResult:
        """_oneloopallbands()

        """
        from smeteravg import SMeterAvg
        results: List[SMeterAvg] = []
        BANDS.values()
        activeBands: List[str] = [bp.bandid for bp in BANDS.values() if bp.is_enabled()]
        nfresult: NFResult = NFResult()
        nfresult.start()
        try:

            for bid in activeBands:
                band_reading: Bandreadings = Bandreadings(bid, self.flex)
                band_reading.doit()
                band_reading.flexradio = None  # make safe for pickleing
                results.append(band_reading.band_signal_strength)
        except Exception as ex:
            print(f'exception1 in _oneloopallbands {str(ex)}')
            raise ex

        try:
            nfresult.end(results)
        except Exception as ex:
            print(f'exception2 in _oneloopallbands {str(ex)}')
            raise ex
        return nfresult

    def oneloop_all_bands(self, testdata: NFResult = None, dups: bool = False):
        """oneloop_all_bands()

        does one iteration of checking all bands

        """
        nfresult: NFResult = None

        if not testdata:
            while True:
                try:
                    nfresult = self._oneloopallbands()
                    break
                except Exception as ve:  # ValueError as ve:
                    print(f'value error in _oneloopallbands: {ve}')
                    continue

        else:
            nfresult = testdata

        if dups:
            self._last_band_readings = nfresult
            self._recordprocdata(nfresult)

        elif (not self._last_band_readings) or nfresult != self._last_band_readings:  # remove close readings
            self._last_band_readings = nfresult
            self._recordprocdata(nfresult)

    def doit(self, runtime=10, interval="30", loops=0, dups: bool = False, testdatafile: str = None):
        """doit runtime=10, interval"""
        from qdatainfo import NFQ
        """doit(runtime="10hr", interval="30", loops=0)

        gets the noise from all measured bands.
        runtime is the time extent the measurements will be taken if loops is 0
        interval is the number of seconds between each run
        loops is the number of times the measurment will be taken and if >0 overrides the runtime

        """
        class IntervalAdj:
            def __init__(self, interval: float):
                self.inter: float = interval
                self.starttime: float = None
                self.endtime: float = None
                pass

            def start(self):
                self.starttime: float = monotonic()

            def end(self):
                self.endtime: float = monotonic()

            def getinterval(self) -> float:
                if self.starttime is None or self.endtime is None:
                    return self.inter
                else:
                    duration: float = self.endtime - self.starttime
                    timeleft: float = self.inter - duration
                    if timeleft < 0.1:
                        # print(f'dur:{duration : .2f}, delay:0.1')
                        return 0.001
                    else:
                        # print(f'dur:{duration : .2f}, tl:{timeleft : .2f}')
                        return timeleft

        # initdata = self.initialize_flex() #if you need to look at the results
        testdl: List[NFQ] = None
        testdlin: List[NFQ] = None
        _allow_dups: bool = dups

        if testdatafile:  # for example 'noisefloordata.pickle'
            with open(testdatafile, 'rb') as jsi:
                testdlin = pickle.load(jsi)
            testdl = testdlin[0: loops]

        if self.stop_event.is_set():
            return
        try:

            self.flex.do_cmd_list(INITIALZE_FLEX)
            # _DT.open()
            first: bool = True
            # interval_adj: float = 0.0
            if loops == 0:
                start_time = datetime.datetime.now()
                self.end_time = start_time + \
                    datetime.timedelta(hours=runtime)
                while datetime.datetime.now() < self.end_time:
                    if testdl:
                        for dta in testdl:
                            self.oneloop_all_bands(
                                testdata=dta, dups=_allow_dups)
                            Sleep(1)
                    else:
                        intadj: IntervalAdj = IntervalAdj(interval)
                        if self.stop_event.is_set():
                            return
                        realint: float = intadj.getinterval()
                        if not first:
                            self.stop_event.wait(realint)
                        else:
                            first = False

                        intadj.start()
                        self.oneloop_all_bands(dups=_allow_dups)
                        intadj.end()

            else:
                if testdl:
                    for dta in testdl:
                        self.oneloop_all_bands(
                            testdata=dta, dups=_allow_dups)
                        Sleep(1)
                else:
                    intadj: IntervalAdj = IntervalAdj(interval)
                    for _ in range(loops):
                        if self.stop_event.is_set():
                            return

                        realint: float = intadj.getinterval()
                        if not first:
                            self.stop_event.wait(realint)
                        else:
                            first = False

                        # print(f'{_}', end='')
                        intadj.start()
                        self.oneloop_all_bands(dups=_allow_dups)
                        intadj.end()

        except Exception as ex:
            print(f'exception in doit {ex}')
            raise ex

        finally:
            pass


def main(stop_events: Mapping[str, CTX.Event], queues: Mapping[str, CTX.JoinableQueue]):
    UI = UserInput()
    NOISE = None

    UI.request(port='com4')
    flexr = Flex(UI)
    initial_state = None
    try:
        if not flexr.open():
            raise (RuntimeError('Flex not connected to serial serial port'))
        print('saving current flex state')
        initial_state = flexr.save_current_state()
        print('initializing dbg flex state')
        flexr.do_cmd_list(INITIALZE_FLEX)
        flexr.close()
        resultQ = queues.get('dataQ')
        stop_event = stop_events.get('acquireData')

        NOISE = Noisefloor(flexr, resultQ, stop_event)
        NOISE.open()
        # loops must be less than 100 as that is the queue size and I am not emptying it here
        NOISE.doit(loops=90, interval=90, dups=True)
        # NOISE.doit(runtime=1, interval=60)
        stop_event.set()

        indata: List[NFQ] = []
        try:

            while True:
                indata.append(resultQ.get(True, 1))
                resultQ.task_done()
        except QEmpty:
            pass  # q is empty
        except Exception as ex:
            print(ex)
            raise ex

        with open('nfqlistdata.pickle', 'wb') as jso:
            pickle.dump(indata, jso)
        unpacked: List[NFResult] = [npq.get() for npq in indata]
        with open('nfrlistdata.pickle', 'wb') as jso:
            pickle.dump(unpacked, jso)
        reads: List[SMeterAvg] = []
        for nfr in unpacked:
            reads.extend(nfr.readings)
        with open('smavflistdata.pickle', 'wb') as jso:
            pickle.dump(reads, jso)

        up0: NFResult = unpacked[0]
        outdata = []
        with open('nfqlistdata.pickle', 'rb') as jsi:
            outdata = pickle.load(jsi)

        brlst: List[Bandreadings] = []
        for nfq in outdata:
            br: Bandreadings = nfq.get()
            brlst.append(br)

        a = indata[0]
        b = outdata[0]

    except(Exception, KeyboardInterrupt) as exc:
        if NOISE:
            NOISE.close()
        UI.close()
        raise exc

    finally:
        print('restore flex prior state')
        flexr.restore_state(initial_state)

        if NOISE:
            NOISE.close()
        UI.close()


if __name__ == '__main__':
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
    THE_LOGGER.info('noisefloor executed as main')
    # LOGGER.setLevel(logging.DEBUG)

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

    try:
        main(STOP_EVENTS, QUEUES)
        normalexit = True
    except(Exception, KeyboardInterrupt) as exc:
        print(exc)
        normalexit = False

    finally:
        if normalexit:
            sys.exit('normal exit')
        else:
            sys.exit('error exit')

