#!/usr/bin/env python3
"""This script prompts for user input for serial port etc."""
import sys
import os
import logging
import logging.handlers
import myserial
import getports


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/userinput'

def _ignore(_ignoreme):
    return

def _pop_test_data(queue, ignore):
    # pylint: disable=W0613
    return queue.pop()

def _inputg(ignore, _a):
    # pylint: disable=W0613
    return input(_a)

_CLOSE_IFD = {True: lambda a: a.close(),
              False: _ignore,}

_USER_INPUT_IFD = {
    True: _pop_test_data,
    False: _inputg,}

class UserInput:
    """UserInput( ctype=controller, testdata=string, testing=TF)

    obtains user input for which serial port to use and a path for
    an input file to be read.

    If only a single serial port is available, it is used by default.
    If no serial port is available it throws an unchecked exception

    if run as __main__

    Displays available prots,
    Obtains user input for the selected port and file (the file info is ignored)
    Attempts to open the port, and if able prints "Requested Port can be opened"
    May also generate an OSError if unable to match the controller baud rate

    comm_port vs serial_port: comm_port is the text name of the port, serial_port
    is a MySerial object.  You should do an open to setup the serial_port Using
    the comm_port value
    """

    def _inputa(self, query):
        return _USER_INPUT_IFD.get(isinstance(self._td, list))(self._td, query)

    def __init__(self, testdata=None, testing=False):
        self.testing = testing
        self.comm_port = ""
        self.inputfn = ""
        ##self.controller_type = ctype
        #if self.controller_type is None:
            #self.serial_port = None
        #else:
        self.serial_port = myserial.MySerial()

        self._td = None
        if testdata:
            if isinstance(testdata, list):
                self._td = testdata
                self._td.reverse()
            else:
                assert "illegal testdata type"

    def __str__(self):
        return '[UserInput: {}, {}]'.format(self.comm_port, self.inputfn)

    def __repr__(self):
        return '[UserInput: {}, {}]'.format(self.comm_port, self.inputfn)

    def request(self):
        """request()

        Request comm port id
        """
        while 1:
            tups = []
            available = getports.GetPorts().get()
            if available and len(available) > 1:
                print('Available comport(s) are: {}'.format(available))
                tups = [(_.strip(), _.strip().lower()) for _ in available]
                useri = self._inputa("Comm Port for SmartCat slice?>").strip()
            elif available:
                tups = [(_.strip(), _.strip().lower()) for _ in available]
                useri = tups[0][1]
            else:
                print('No available ports')
                self.close()
                raise Exception(" no available ports")

            hits = [t for t in tups if useri.lower() in t]
            if hits:
                [_port] = hits
                self.comm_port = _port[0]
                print('Using serial port: {}'.format(self.comm_port))
                break

        self.inputfn = ''

    def close(self):
        """close()

        Closes the serial port if it is open
        """
        _CLOSE_IFD.get(self.serial_port.isOpen())(self.serial_port)


    def open(self, detect_br=True):
        """open()

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

        if not self.comm_port:
            raise AttributeError('comport not specified')
        sport = self.serial_port
        try:
            sport.port = self.comm_port  # '/dev/ttyACM0'
            sport.timeout = .2
            sport.baudrate = 19200
            _CLOSE_IFD.get(self.serial_port.isOpen())(self.serial_port)
            sport.open()

        except myserial.serial.SerialException as sex:
            self.comm_port = ""
            print(sex)
            return False
        _detect_br = detect_br or self.testing
        if _detect_br and not sport.find_baud_rate():
            raise OSError('Unable to match controller baud rate')
        return True


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
    LC_HANDLER.setLevel(logging.DEBUG)  #(logging.ERROR)
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
    #LOGGER.setLevel(logging.DEBUG)
    UI = UserInput()
    try:
        UI.request()
        UI.open()
        print("Requested Port can be opened")
        UI.close()

    except(Exception, KeyboardInterrupt) as exc:
        UI.close()
        sys.exit(str(exc))
