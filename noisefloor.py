#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os
import logging
import logging.handlers
import datetime
# import math
import time
import multiprocessing as mp
# from statistics import mean
# import mysql.connector as mariadb
from userinput import UserInput
# from smeter import SMeter, _SREAD
from bandreadings import Bandreadings
from flex import Flex
#import dbtools
import postproc
#from trackermain import QUEUES, STOP_EVENTS, CTX

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/noiseFloor'

CTX = mp.get_context('spawn')  # threading context
print('CTX should not be defined here ******************************')

#_DT = dbtools.DBTools()
#_DB = _DT.dbase
#_CU = _DT.cursor


# def threadrun(threadLock):
# threadLock.acquire()

# try:
# UI.request()
# UI.open()
#print("Requested Port can be opened")
#FLEX = Flex(UI)
#NOISE = Noisefloor(UI)
# NOISE.open()
#NOISE.doit(loops=10, interval=30)
# NOISE.close()

# except(Exception, KeyboardInterrupt) as exc:
# if NOISE:
# NOISE.close()
# UI.close()
# sys.exit(str(exc))

# finally:
# if NOISE:
# NOISE.close()
# UI.close()
# sys.exit(str(exc))


# def find_band(wave_length):
# """find_band(wave_length)

# """
# return math.trunc(round(wave_length) / 10) * 10


# def _process_raw_data(rawdata, band):
# """_process_raw_data(rawdata,band)

# """
#tfrq = rawdata[0:1][0]
#sm_avr = SMeterAvg(rawdata[1:], band)
# return (tfrq, sm_avr)

def _recordprocdata(bandreadings_lst):
    """_recordprocdata(bandreadings)

    bandreadings_lst is a list of Bandreadings
    """

    #recid = _DT.getrecid()

    # for bandreading in bandreadings_lst:
    # bandreading.savebr(recid)


# should send this to the dataqueue
    # _DB.commit()


# def getrecid():
    # """getrecid()

    # """
    #date_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #sql = 'INSERT INTO TIMES(timescol) Values (\"{}\");'.format(date_string)
    # _CU.execute(sql)
    # _DB.commit()
    #_CU.execute('SELECT RECID FROM TIMES ORDER BY RECID DESC LIMIT 1;')
    #records = _CU.fetchall()
    # return records[0][0]

# def _get_cat_data(cmd_list, freq):
    # """_get_cat_data(cmd_list)

    # returns a list of the raw or processed result from Cat results

    # """
    #results = []
    # for cmd in cmd_list:
    # if cmd[0][0:4] == 'wait':
    #delay = float(cmd[0][4:])
    # time.sleep(delay)
    # continue
    #result = UI.serial_port.docmd(cmd[0])
    # if cmd[1]:  # process the result if provided
    #_ = result.split(';')
    #vals = None
    # if len(_) > 2:
    #vals = [int(ss[4:]) for ss in _]
    #avg = int(round(sum(vals) / len(vals)))
    #result = 'ZZSM{:03d};'.format(avg)

    #result = cmd[1]((result, freq))
    # results.append(result)

    # return results


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
        self._last_band_readings = None
        if testdata:
            if isinstance(testdata, list):
                self._td = testdata
                self._td.reverse()
            else:
                assert "illegal testdata type"

        self.end_time = None
        self.initial_state = None
        self.is_open = False

    def __str__(self):
        return '[UserInput: {}, {}]'.format('junk0', 'junk1')

    def __repr__(self):
        return '[UserInput: {}, {}]'.format('junk0', 'junk1')

    def open(self, detect_br=False) -> bool:
        """open( detect_br)

        Configures and opens the serial port if able, otherwise
         displays error with reason.
         (if the serial port is already open, closes it and re opens it)

        If the serial port is opened and if detect_br: the baud rate of the controller is
        found and the serial port so set.

        If detect_br is True, the baud rate will be detected by establishing
        communication with the controller

        If the serial port is opened, returns True, False otherwise

        thows exception if no baud rate is found
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
            self.flex.restore_state(self.initial_state)
            self._ui.comm_port = ""
            # self.dbase.close()
            print(sex)
            self.is_open = False

        return self.is_open

    def close(self) -> bool:
        """close()

        """
        if not self.is_open:
            return False

        self.flex.restore_state(self.initial_state)
        self.flex.close()
        self.is_open = False
        # self.dbase.close()
        return True

    def oneloop_all_bands(self):
        """oneloop_all_bands()

        does one iteration of checking all bands

        """
        results = []
        freq_list = postproc.FREQUENCIES[:]
        freq_in_band = []
        for _ in range(0, len(freq_list), 3):
            freq_in_band.append(freq_list[_:_ + 3])

        for _freq in freq_in_band:  # go through all the scanned bands
            run = True
            count = 5  # only 5 attempts to get a reasonable signal
            band_reading = None
            while run:
                band_reading = Bandreadings(_freq, self.flex)
                band_reading.doit()
                sigs = band_reading.band_signal_strength
                run = sigs.signal_st.get('stddv') > 1.5 and count > 0
                if run and count < 2:
                    # self.changefreqs(sigs)
                    pass
                count -= 1

            results.append(band_reading)

        if (not self._last_band_readings) or results != self._last_band_readings:
            self._last_band_readings = [results]
            _recordprocdata(results)

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

    def doit(self, runtime="10hr", interval="30", loops=0):
        """doit(runtime="10hr", interval="30", loops=0)

        gets the noise from all measured bands.
        runtime is the time extent the measurements will be taken if loops is 0
        interval is the number of seconds between each run
        loops is the number of times the measurment will be taken and if >0 overrides the runtime

        """
        # initdata = self.initialize_flex() #if you need to look at the results

        try:

            self.flex.do_cmd_list(postproc.INITIALZE_FLEX)
            # _DT.open()
            if loops == 0:
                start_time = datetime.datetime.now()
                self.end_time = start_time + \
                    datetime.timedelta(hours=runtime)
                while datetime.datetime.now() < self.end_time:
                    self.oneloop_all_bands()
                time.sleep(interval)
            else:
                for _ in range(loops):
                    self.oneloop_all_bands()
                time.sleep(interval)

        finally:
            pass
            # flexr.restore_state(self.initial_state)
            # _DT.close()


def main(stop_events, queues):
    UI = UserInput()
    NOISE = None

    UI.request(port='com4')
    flexr = Flex(UI)
    initial_state = None
    try:
        flexr.open()
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
        NOISE.close()

    except(Exception, KeyboardInterrupt) as exc:
        if NOISE:
            NOISE.close()
        UI.close()
        raise exc

    finally:
        print('restore flex prior state')
        flexr.restore_state(initial_state)
        flexr.close()
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
    THE_LOGGER.info('userinput executed as main')
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

    except(Exception, KeyboardInterrupt) as exc:
        sys.exit(str(exc))

    finally:
        sys.exit('normal exit')

