#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os
from typing import List, Sequence, Dict, Mapping
import logging
import logging.handlers
import datetime
import jsonpickle
# import math
import time
from queue import Empty as QEmpty
import multiprocessing as mp
# from statistics import mean
# import mysql.connector as mariadb
from userinput import UserInput
# from smeter import SMeter, _SREAD
from bandreadings import Bandreadings
from flex import Flex
#import dbtools
import postproc
import noisefloor
from postproc import BANDS, BandPrams
from qdatainfo import NFQ
#from trackermain import QUEUES, STOP_EVENTS, CTX


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/noiseFloor'

CTX = mp.get_context('spawn')  # threading context
print('CTX should not be defined here ******************************')


class NFResult:
    """NFResult()

    holds the result from running _oneloopallbands()
    """

    def __init__(self):
        self.starttime: str = 'Not Started'
        self.endtime: str = 'Not Ended'
        self.readings: List[Bandreadings] = []
        self._started: bool = False
        self._ended: bool = False

    def __str__(self):
        if self._started and self._ended:
            stdevlst = [
                (
                    r.bandid,
                    r.band_signal_strength.signal_st.get('sl'),
                    r.band_signal_strength.signal_st.get('stddv'),)
                for r in self.readings
            ]
            readings: str = f'Band Noise Readings\n{self.starttime}\n'
            for _ in stdevlst:
                readings += f'    b:{_[0]}, {_[1]}, {_[2] :.2f}\n'

            readings += f'{self.endtime}\n'
            return readings

        if self._started:
            return f'band readings started at {self.starttime}'
        return 'Not Started'

    def __repr__(self):
        return f'Noisefloor: {self.__str__()}'

    def __eq__(self, other):
        """__eq__(self,other)

        Equality does not compare the date/time values, only the
        condition of started and ended and the bandid, sl, and stddv
        """
        if self._ended ^ other._ended or len(self.readings) != len(other.readings):
            return False

        one2one = zip(
            [(
                r.bandid,
                r.band_signal_strength.signal_st.get('sl'),
                r.band_signal_strength.signal_st.get('stddv'),
            )
                for r in self.readings],
            [(
                r.bandid,
                r.band_signal_strength.signal_st.get('sl'),
                r.band_signal_strength.signal_st.get('stddv'),
            )
                for r in other.readings]
        )

        result = True

        for s, o in one2one:
            result = result and s[0] == o[0] and s[1] == o[1]
            dif = s[2] - o[2]
            if dif < 0.0:
                dif = o[2] - s[2]
            result = result and dif < 0.3
            # if not result:
            # return result
        return result

    def __ne__(self, other):
        return not self.__eq__(other)

    # def __lt__(self, other):
        # pass

    # def __gt__(self, other):
        # pass

    # def __le__(self, other):
        # pass

    # def __ge__(self, other):
        # pass

    def start(self):
        if not self._started:
            self.starttime = time.strftime(
                "%b %d %Y %H:%M:%S", time.localtime())
            self._started = True

    def end(self, result: Sequence[Bandreadings]):
        if self._started and not self._ended:
            self.endtime = time.strftime(
                "%b %d %Y %H:%M:%S", time.localtime())
            self.readings = result[:]
            self._ended = True

    def completed(self) -> bool:
        return self._started and self._ended

    def gen_sql(self):
        pass


class Noisefloor:
    """Noisefloor(flex, out_queue, stop_event, testdata=None, testing=False)
    """

    def __init__(self, flex: Flex, out_queue: CTX.JoinableQueue, stop_event: CTX.Event, testdata=None, testing=False):
     #   def __init__(self, userI, testdata=None, testing=False):

        self.flex = flex
        self._ui = flex._ui
        self._td = None
        self.out_queue = out_queue
        self.stop_event = stop_event
        self._last_band_readings: noisefloor.NFResult = None
        if testdata:
            if isinstance(testdata, list):
                self._td = testdata
                self._td.reverse()
            else:
                assert "illegal testdata type"

        self.end_time = None
        self.initial_state = None
        self.is_open = False
        self.testdata = testdata

    def __str__(self):
        return '[UserInput: {}, {}]'.format('junk0', 'junk1')

    def __repr__(self):
        return '[UserInput: {}, {}]'.format('junk0', 'junk1')

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

            # self.dbase.open()

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

    def _recordprocdata(self, noisefloordata: Sequence[Bandreadings]):
        """_recordprocdata()

        Sends the changed band data to the data queue
        """
        # for br in noisefloordata:
        #br.flexradio = None
        _nfq = NFQ(noisefloordata)
        self.out_queue.put(_nfq)
        # print (f'queued {noisefloordata}')

    def _oneloopallbands(self) -> noisefloor.NFResult:
        """_oneloopallbands()

        """

        results: List[Bandreadings] = []
        postproc.BANDS.values()
        activeBands: List[str] = [bp.bandid for bp in BANDS.values() if bp.is_enabled()]
        nfresult: noisefloor.NFResult = noisefloor.NFResult()
        nfresult.start()
        for bid in activeBands:
            band_reading = Bandreadings(bid, self.flex)
            band_reading.doit()
            band_reading.flexradio = None  # make safe for pickleing
            results.append(band_reading)
        nfresult.end(results)
        return nfresult

    def oneloop_all_bands(self, testdata: noisefloor.NFResult = None):
        """oneloop_all_bands()

        does one iteration of checking all bands

        """
        nfresult: noisefloor.NFResult = None

        if not self.testdata:
            while True:

                try:
                    nfresult = self._oneloopallbands()
                    break
                except ValueError as ve:
                    print(f'value error in _oneloopallbands: {ve}')
                    continue

        else:
            nfresult = testdata

        if (not self._last_band_readings) or nfresult != self._last_band_readings:
            self._last_band_readings = nfresult
            self._recordprocdata(nfresult)

    # def save_flex_state(self):
        #self.saved_flex_state = {}

    # def restore_flex_state(self):
        # print(self.saved_flex_state)

    # def initialize_flex(self):
        # """initialize_flex()

        # """
        #_ui = self._ui
        #results = []
        # for cmd, proc in postproc.INITIALZE_FLEX.items():
        # for cmd, proc in postproc.INITIALZE_FLEX.items():
        #result = _ui.serial_port.docmd(cmd)
        # if proc:
        #result = proc(result)

        # results.append(result)
        # return results

    def doit(self, runtime=10, interval="30", loops=0):
        """doit(runtime="10hr", interval="30", loops=0)

        gets the noise from all measured bands.
        runtime is the time extent the measurements will be taken if loops is 0
        interval is the number of seconds between each run
        loops is the number of times the measurment will be taken and if >0 overrides the runtime

        """
        # initdata = self.initialize_flex() #if you need to look at the results
        testdl: List[noisefloor.NFResult] = None

        if self.testdata:
            with open('noisefloordata.json', 'r') as jsi:
                testdl = jsonpickle.decode(jsi.readline())

        if self.stop_event.is_set():
            return
        try:

            self.flex.do_cmd_list(postproc.INITIALZE_FLEX)
            # _DT.open()
            if loops == 0:
                start_time = datetime.datetime.now()
                self.end_time = start_time + \
                    datetime.timedelta(hours=runtime)
                while datetime.datetime.now() < self.end_time:
                    if testdl:
                        for dta in testdl:
                            self.oneloop_all_bands(testdata=dta)
                            time.sleep(1)
                    else:
                        self.oneloop_all_bands()
                        if self.stop_event.is_set():
                            return
                        self.stop_event.wait(interval)
                        if self.stop_event.is_set():
                            return
            else:
                if testdl:
                    for dta in testdl:
                        self.oneloop_all_bands(testdata=dta)
                        time.sleep(1)
                else:
                    for _ in range(loops):
                        print(f'{_}: ', end='')
                        self.oneloop_all_bands()
                        if self.stop_event.is_set():
                            return
                        self.stop_event.wait(interval)
                        if self.stop_event.is_set():
                            return

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
        flexr.do_cmd_list(postproc.INITIALZE_FLEX)
        flexr.close()
        resultQ = queues.get('dataQ')
        stop_event = stop_events.get('acquireData')

        NOISE = Noisefloor(flexr, resultQ, stop_event)
        NOISE.open()
        NOISE.doit(loops=10, interval=60)
        #NOISE.doit(runtime=1, interval=60)
        stop_event.set()

        indata = []
        try:

            while True:
                indata.append(resultQ.get(True, 1))
                resultQ.task_done()
        except QEmpty:
            pass  # q is empty
        except Exception as ex:
            print(ex)
            raise ex

        print(indata)
        #id = indata[0]

        with open('noisefloordata.json', 'w') as jso:  # jsonpickle.encode
            _ = jsonpickle.encode(indata)
            jso.write(_)

        with open('noisefloordata.json', 'r') as jsi:
            aa = jsi.readline()
        cpybss = jsonpickle.decode(aa)

        b = 0

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

    QUEUES = {
        # from data acquisition threads, received by the aggragator thread
        'dataQ': CTX.JoinableQueue(maxsize=100),
        # database commands generateed (usually) ty the aggrator thread
        'dbQ': CTX.JoinableQueue(maxsize=100),
        # written to by the aggrator thread, read by the data processor which generates sql commands to dbq
        'dpQ': CTX.JoinableQueue(maxsize=100)
    }

    STOP_EVENTS = {
        'acquireData': CTX.Event(),
        'trans': CTX.Event(),
        'dbwrite': CTX.Event(),
        'agra': CTX.Event(),
    }
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

