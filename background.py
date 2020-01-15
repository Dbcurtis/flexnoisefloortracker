#!/usr/bin/env python3

"""This script prompts for user input for serial port etc."""

import os
import logging
import logging.handlers

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/background'

class Background:
    """Noisefloor()
    """

    def __init__(self, userI, testdata=None, testing=False):
        _s = self
        _s._ui = userI
        _s._td = None
        if testdata:
            if isinstance(testdata, list):
                self._td = testdata
                self._td.reverse()
            else:
                assert "illegal testdata type"

    def __str__(self):
        return '[UserInput: {}, {}]'.format('junk0', 'junk1')

    def __repr__(self):
        return '[UserInput: {}, {}]'.format('junk0', 'junk1')

def main():
    pass


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
    main()
