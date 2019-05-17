#!/usr/bin/env python3
""" TO BE DONE """
import os
import logging
import logging.handlers
import serial
import serial.tools.list_ports

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/getports'



class GetPorts:
    """GetPorts Class determines what communication ports exist on the executing computer

    The version of serial is used to determine how list port works.

    Usage:
    devs = getports.GetPorts().get()

    every call to get() refreshes the port tuple.
    Thus, you can take out and insert ports at any time.
    """


    def __init__(self):
        self.devs = []
        LOGGER.debug('Created GetPorts')
        self._old_serial = False
        try:
            _j = serial.__version__
        except AttributeError:
            self._old_serial = True
        if self._old_serial:
            LOGGER.debug('Detected Python 3.4')
            raise NameError('require Python 3.6 and higher')

    def get(self):
        """get()

        returns a list of serial(?) ports
        """
        LOGGER.debug('entered get')
        ports = serial.tools.list_ports.comports()
        devs = []

        #if self._old_serial:
            #devs = [p for p in [port[0] for port in ports]]
        #else:
        devs = [port.device for port in ports]

        self.devs = [p for p in devs]
        LOGGER.debug('exited get with %s', self.devs)
        return self.devs


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
    THE_LOGGER.info('getports executed as main')
    #LOGGER.setLevel(logging.DEBUG)
    PORTS = GetPorts().get()
    if PORTS:
        print(PORTS)
    else:
        print("No ports found or all found ports busy")
