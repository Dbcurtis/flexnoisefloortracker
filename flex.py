#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""


import os
import logging
import logging.handlers
import time
# from statistics import mean
#import mysql.connector as mariadb
from userinput import UserInput
# from smeter import SMeter, _SREAD
# from bandreadings import Bandreadings
#import dbtools
#import postproc

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/flex'

FLEX_CAT_ALL = frozenset(
    [
        'ZZAG', 'ZZAI', 'ZZAR', 'ZZAS', 'ZZBI', 'ZZDE', 'ZZFA', 'ZZFB', 'ZZFI',
        'ZZFJ', 'ZZFR', 'ZZFT', 'ZZGT', 'ZZIF', 'ZZLB', 'ZZLE', 'ZZLF', 'ZZMA',
        'ZZMD', 'ZZME', 'ZZMG', 'ZZNL', 'ZZNR', 'ZZPC', 'ZZRC', 'ZZRD', 'ZZRG',
        'ZZRT', 'ZZRU', 'ZZRW', 'ZZRX', 'ZZRY', 'ZZSM', 'ZZSW', 'ZZTX', 'ZZXC',
        'ZZXG', 'ZZXS',
    ]
)

FLEX_CAT_WRITE = frozenset(
    ['ZZFR', 'ZZFT', 'ZZPE', 'ZZRC', 'ZZRD',
        'ZZRU', 'ZZSM', 'ZZSW', 'ZZTX', 'ZZXC', ]
)

FLEX_CAT_READ_ONLY = FLEX_CAT_ALL - FLEX_CAT_WRITE


class Flex:
    """

    represents the state of the flex radio.
    """

    def __init__(self, ui):
        """Constructor
        ui is a UserInput object that is connected to the CAT port for the flex
        """
        self._ui = ui
        self.is_open = False
        self.saved_state = []

    def __str__(self):
        cp = self._ui.comm_port if self._ui.comm_port else "unspecified"
        return f'Flex cat: {cp}, opened: {self.is_open}'

    def __repr__(self):
        cp = self._ui.comm_port if self._ui.comm_port else "unspecified"
        return f'[Flex] Flex cat: {cp}, opened: {self.is_open}'

    def open(self, detect_br=False):
        """open(detect_br)

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

        try:
            self._ui.open(detect_br)
            self.is_open = self._ui.serial_port.is_open

        except Exception as sex:
            self._ui.comm_port = ""
            print(sex)
            return False

        return True

    def do_cmd(self, cmd):
        """do_cmd(cmd)

        """
        if cmd[0:4] not in FLEX_CAT_ALL:
            return '??;'
        if ';' != cmd[-1]:
            cmd = f'{cmd};'
        return self._ui.serial_port.docmd(cmd)

    def do_cmd_list(self, cset):
        """do_cmd_list(clist)

        cset is a list or a set.
        If a set, it is converted into a list and sorted.

        """
        resultlst = []
        if not self.is_open:
            return self.saved_state

        clist = [_ for _ in cset]
        if isinstance(cset, set):
            clist.sort()

        # resultlst = [self.do_cmd(cmd) for cmd in clist]
        resultlst = [_ for _ in [self.do_cmd(
            cmd) for cmd in clist] if _ != '?;']

        return resultlst[:]

    def save_current_state(self):
        """save_current_state()

        """
        self.saved_state = self.do_cmd_list(FLEX_CAT_READ_ONLY)
        return self.saved_state[:]

    def restore_saved_state(self):
        """restore_saved_state()

        """
        self.restore_state(self.saved_state)

    def restore_state(self, cmdlst):
        """restore_state()

        """
        results = []
        if self._ui.serial_port.is_open and cmdlst:
            for cmd in cmdlst:
                if cmd[0:4] in 'ZZIF':
                    continue
                cmdreply = self._ui.serial_port.docmd(cmd)
                results.append(cmdreply)
            self.save_current_state()
        return results

    def close(self):
        """close()

        """
        self._ui.close()
        self.is_open = self._ui.serial_port.is_open

    def get_cat_data(self, cmd_list, freq):
        """get_cat_data(cmd_list)

        returns a list of the raw or processed result from Cat results

        """
        results = []
        for cmd in cmd_list:
            if cmd[0][0:4] == 'wait':
                delay = float(cmd[0][4:])
                time.sleep(delay)
                continue
            if cmd[0][0:4] not in FLEX_CAT_ALL:
                raise Exception('illegal flex command')
            result = self._ui.serial_port.docmd(cmd[0])
            if cmd[1]:  # process the result if provided
                _ = result.split(';')
                vals = None
                if len(_) > 2:
                    vals = [int(ss[4:]) for ss in _]
                    avg = int(round(sum(vals) / len(vals)))
                    result = 'ZZSM{:03d};'.format(avg)

                result = cmd[1]((result, freq))
            results.append(result)

        return results


def main():
    """main()

    """

    ui = UserInput()
    ui.request(port='com4')
    flex = None
    try:

        flex = Flex(ui)
        flex.open()
    finally:
        if flex:
            flex.close()


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
    THE_LOGGER.info('flex executed as main')
    # LOGGER.setLevel(logging.DEBUG)
    #UI = UserInput()
    #NOISE = None
    try:
        main()

    except(Exception, KeyboardInterrupt) as exc:
        pass
