#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import sys
import os
from typing import Any, Tuple, Sequence, List, Set, FrozenSet
#from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque, Iterable
import logging
import logging.handlers
from time import sleep as Sleep
from userinput import UserInput
from smeter import SMeter, SMArgkeys


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/flex'

"""FLEX Commands:

ZZAG Reads / Sets VFO A Audio Gain (0-100)
ZZAI Auto Information State (on/off)
ZZAR Reads / Sets VFO A AGC Threshold (0-100)
ZZAS Reads / Sets VFO B AGC Threshold (0-100)
ZZBI Reads / Sets Binaural RX State (On / Off)
ZZDE Reads / Sets VFO A Diversity (DIV) state (On / Off) [FLEX-6700 only]
ZZFA Reads / Sets VFO A Frequency (11 digit Hz)
ZZFB Reads / Sets VFO B Frequency (11 digit Hz)
ZZFI Reads / Sets VFO A DSP Filter Index
ZZFJ Reads / Sets VFO B DSP Filter Index
ZZFR Toggle VFO A/B Active  -- NOT USED
ZZFT Toggle VFO A/B Transmit -- NOT USED
ZZGT Reads / Sets VFO A AGC Mode
ZZIF Reads Transceiver Status
ZZLB Reads / Sets VFO A Audio Pan (0-100, Left to Right)
ZZLE Reads / Sets VFO B Audio Gain (0-100)
ZZLF Reads / Sets VFO B Audio Pan (0-100, Left to Right)
ZZMA Reads / Sets VFO A Mute (On / Off)
ZZMD Reads / Sets VFO A DSP Mode
ZZME Reads / Sets VFO B DSP Mode
ZZMG Reads / Sets Transmitter Mic Gain (0-100)
ZZNL Reads / Sets VFO A Wide Noise Blanker (WNB) Threshold (0-100)
ZZNR Reads / Sets VFO A Noise Reduction (NR) State (On / Off)
ZZPC Reads / Sets the RF Power Drive Level (0-100)
ZZRC Clears RIT
ZZRD Decrements RIT frequency
ZZRG Reads / Sets VFO A RIT Frequency (+/- 5 digit Hz)
ZZRT Reads / Sets VFO A RIT State (On / Off)
ZZRU Increments the RIT frequency
ZZRW Reads / Sets VFO B RIT Frequency (+/- 5 digit Hz)
ZZRX Reads Receive State (On / Off) [inverse of MOX]
ZZRY Reads / Sets VFO B RIT Frequency (+/- 5 digit Hz)
ZZSM Read the S-Meter
ZZSW Set Transmit VFO (0=A, 1=B)
ZZTX Set MOX State (On / Off)
ZZXC Clear XIT Frequency
ZZXG Read / Set VFO A XIT Frequency (+/- 5 digit Hz)
ZZXS Reads / Sets XIT State (On / Off)
"""

FLEX_CAT_ALL: FrozenSet[str] = frozenset(
    [
        'ZZAG', 'ZZAI', 'ZZAR', 'ZZAS', 'ZZBI', 'ZZDE', 'ZZFA', 'ZZFB', 'ZZFI',
        'ZZFJ', 'ZZFR', 'ZZFT', 'ZZGT', 'ZZIF', 'ZZLB', 'ZZLE', 'ZZLF', 'ZZMA',
        'ZZMD', 'ZZME', 'ZZMG', 'ZZNL', 'ZZNR', 'ZZPC', 'ZZRC', 'ZZRD', 'ZZRG',
        'ZZRT', 'ZZRU', 'ZZRW', 'ZZRX', 'ZZRY', 'ZZSM', 'ZZSW', 'ZZTX', 'ZZXC',
        'ZZXG', 'ZZXS',
    ]
)

FLEX_CAT_WRITE: FrozenSet[str] = frozenset(  # this variable is badly named
    ['ZZFR', 'ZZFT', 'ZZPE', 'ZZRC', 'ZZRD',
        'ZZRU', 'ZZSM', 'ZZSW', 'ZZTX', 'ZZXC', ]
)

FLEX_CAT_READ_ONLY = FLEX_CAT_ALL - FLEX_CAT_WRITE
# which is \
# 'ZZRY', 'ZZNR', 'ZZMA', 'ZZAG', 'ZZRX', 'ZZLB', 'ZZXS', 'ZZDE', \
# 'ZZBI', 'ZZMG', 'ZZFA', 'ZZME', 'ZZPC', 'ZZFI', 'ZZRG', 'ZZRW', \
# 'ZZFJ', 'ZZLE', 'ZZAR', 'ZZRT', 'ZZGT', 'ZZAI', 'ZZFB', 'ZZIF', \
# 'ZZLF', 'ZZXG', 'ZZNL', 'ZZMD', 'ZZAS'


class Flex:
    """

    represents the state of the flex radio.
    """

    def __init__(self, ui: UserInput):
        """Constructor
        ui is a UserInput object that is connected to the CAT port for the flex
        """
        self._ui: UserInput = ui
        self.is_open: bool = False
        self.saved_state: List[str] = []

    def __str__(self):
        cp = self._ui.comm_port if self._ui.comm_port else "unspecified"
        return f'Flex cat: {cp}, opened: {self.is_open}'

    def __repr__(self):
        cp = self._ui.comm_port if self._ui.comm_port else "unspecified"
        return f'[Flex] Flex cat: {cp}, opened: {self.is_open}'

    def open(self, detect_br: bool = False) -> bool:
        """open(detect_br)

        Configures and opens the serial port if able, otherwise
         displays error with reason.
         (if the serial port is already open, closes it and re opens it)

        If the serial port is opened and if detect_br: the baud rate of the controller is
        found and the serial port so set.

        If detect_br is True, the baud rate will be detected by establishing
        communication with the controller

        If the serial port is opened, and communicating with the flex returns True, False otherwise

        thows exception if no baud rate is found
        """
        result: bool = None
        try:
            self._ui.open(detect_br)
            self.is_open = self._ui.serial_port.is_open
            # check if port is connected to Flex
            repl: str = self.do_cmd('ZZAI;')
            result: bool = repl.startswith('ZZAI')
            repl = self.do_cmd('ZZFA;')
            initfreq: int = int(repl[4:-1])
            cmd: str = f'ZZFA{int(initfreq + 30000) :011d};'
            # testres = self.do_cmd(cmd)
            if self.do_cmd(cmd) != cmd:
                raise Exception('Slice A is Locked, aborting')

            self.do_cmd(repl)  # restore orig freq

        except Exception as sex:
            self._ui.comm_port = ""
            print(sex)
            result = False

        return result

    def do_cmd(self, cmd: str) -> str:
        """do_cmd(cmd)

        """
        if cmd[0:4] not in FLEX_CAT_ALL:
            return '??;'
        if ';' != cmd[-1]:
            cmd = f'{cmd};'
        return self._ui.serial_port.docmd(cmd)

    def do_cmd_list(self, cset: Sequence) -> List[str]:
        """do_cmd_list(clist)

        cset is a list or a set.
        If a set, it is converted into a list and sorted.

        """
        resultlst: List[str] = []
        if not self.is_open:
            return self.saved_state

        clist = [_ for _ in cset]
        if isinstance(cset, set):
            clist.sort()

        """expected ?
        ZZFJ VFO B DSP Filter Index
        ZZAS VFO B AGC Threshold (0-100)
        ZZDE VFO A Diversity (DIV) state (On / Off) [FLEX-6700 only]
        ZZLF VFO B Audio Pan (0-100, Left to Right)
        ZZME VFO B DSP Mode
        ZZLE VFO B Audio Gain (0-100)
        ZZRY VFO B RIT Frequency
        ZZFB VFO B Frequency (11 digit Hz)
        ZZRW VFO B RIT Frequency
        """

        resultlst = [_ for _ in [self.do_cmd(
            cmd) for cmd in clist] if _ != '?;']

        return resultlst[:]

    def save_current_state(self) -> List[str]:
        """save_current_state()

        """
        self.saved_state = self.do_cmd_list(FLEX_CAT_READ_ONLY)
        return self.saved_state[:]

    def restore_saved_state(self):
        """restore_saved_state()

        """
        self.restore_state(self.saved_state)

    def restore_state(self, cmdlst: List[str]) -> List[str]:
        """restore_state()

        TBD

        """
        results: List[str] = []
        if self._ui.serial_port.is_open and cmdlst:
            cmd: str = None
            for cmd in cmdlst:
                if cmd[0:4] in 'ZZIF':
                    continue
                cmdreply: str = self._ui.serial_port.docmd(cmd)
                results.append(cmdreply)
            self.save_current_state()
        return results

    def close(self):
        """close()

        TBD

        """
        self._ui.close()
        self.is_open = self._ui.serial_port.is_open

    def get_cat_dataA(self, cmd_list: List[Tuple[Any, ...]]) -> List[Any]:
        results: List[SMeter] = []
        freq = None

        for cmdt in cmd_list:
            result = None
            c: str = cmdt.cmd[0:4]
            if c == 'wait':
                delay = float(cmdt.cmd[4:])
                Sleep(delay)
                continue

            if c not in FLEX_CAT_ALL:
                raise ValueError('illegal flex command')

            result = self._ui.serial_port.docmd(cmdt.cmd)
            if c == 'ZZFA':
                while not result.startswith('ZZFA'):
                    result = self._ui.serial_port.docmd(cmdt.cmd)
                _ = cmdt.cmd[4:-1]  # get ascii rep of the frequency
                freq = int(_)

            if cmdt.fn:  # process the result if provided
                _ = result.split(';')
                vals = None
                if len(_) > 2:
                    # extract the results from the command
                    try:
                        vals = [int(ss[4:]) for ss in _ if ss]
                    except ValueError as ve:
                        raise ve
                    # and get the average
                    avg: float = int(round(sum(vals) / len(vals)))
                    result = f'ZZSM{avg :03d};'  # .format(avg)

                # process the results by code in cmd[1]
                result = cmdt.fn((result, freq))
            results.append(result)

        return results

    def get_cat_data(self, cmd_list: List[Tuple[Any, ...]], freq: int) -> List[str]:
        """get_cat_data(cmd_list, freq)
        cmd_list is a list of Tuples

        returns a list of the raw or processed result from Cat results

        this differes from get_cat_dataA by how?

        """
        results: List[str] = []
        cmdt: str = None
        for cmdt in cmd_list:
            if cmdt.cmd[0:4] == 'wait':
                delay = float(cmdt.cmd[4:])
                Sleep(delay)
                continue

            if cmdt.cmd[0:4] not in FLEX_CAT_ALL:
                raise ValueError('illegal flex command')

            result: str = self._ui.serial_port.docmd(cmdt.cmd)
            if cmdt.fn:  # process the result if routine is provided
                _ = result.split(';')
                vals = None
                if len(_) > 2:
                    # extract the results from the command
                    vals = [int(ss[4:]) for ss in _ if ss]
                    # and get the average
                    avg = int(round(sum(vals) / len(vals)))
                    result = f'ZZSM{avg :03d};'  # .format(avg)

                # process the results by code in cmd[1]
                result = cmdt.fn((result, freq))
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
    # UI = UserInput()
    # NOISE = None
    try:
        main()
        normalexit = True
    except(Exception, KeyboardInterrupt) as exc:
        print(exc)
        normalexit = False

    finally:
        if normalexit:
            sys.exit('normal exit')
        else:
            sys.exit('error exit')
