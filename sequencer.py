#!/usr/bin/env python3.7
"""
stuff to provide a time scheduler
"""
from __future__ import annotations
import os
import logging
import logging.handlers
from typing import Deque
#from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque, Iterable
from collections import deque
from multiprocessing import freeze_support
from time import monotonic
#from queue import Empty as QEmpty, Full as QFull


LOGGER = logging.getLogger(__name__)
LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/sequencer'


class Sequencer:
    """Sequencer(delayseconds:float)

    Sets up a 20 repratition delayseconds apart  The repetition stays at 20
    resolution is about .5 second (not checked, but guessed)
    """

    def __init__(self, delayseconds: float):
        self.delayseconds: float = delayseconds
        _nowis: float = monotonic()
        self._to_do_sched: Deque[float] = deque(
            [_nowis + t * delayseconds for t in range(1, 21)])  # specifies the first 20 reps
        self.skipped: int = 0

    def do_it_now(self) -> bool:
        """ do_it_now()

        Decides if it is time to do something on a todo schedule.  If one or more scheduled time(s) is missed,
        return true, and all missed times are removed from the schedule, and the schedule extended into the future
        by the number of missed times.

        """
        _nowis: float = monotonic()
        if self._to_do_sched[0] > _nowis:  # if next scheuled is not yet
            return False

        # for each schedled time < current,
        self.skipped = 0
        while self._to_do_sched[0] < _nowis:
            self.skipped += 1
            self._to_do_sched.popleft()   # remove the past scheduled time
            # and add another scheduled time in the future.
            self._to_do_sched.append(
                self._to_do_sched[-1] + self.delayseconds)

        return True

    def get_nxt_wait(self) -> float:
        """get_nxt_wait()

         get the time to wait for the next event on the todo schedule
        """
        _nextt: float = self._to_do_sched[0]
        _nowis: float = monotonic()

        _nextt -= _nowis
        _nextt = 0.0 if _nextt < 0.0001 else _nextt
        return _nextt


def main():
    pass


if __name__ == '__main__':
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
    LC_FORMATTER = logging.Formatter(
        '%(name)s: %(levelname)s - %(message)s')
    LC_HANDLER.setFormatter(LC_FORMATTER)
    LF_HANDLER.setFormatter(LF_FORMATTER)
    THE_LOGGER = logging.getLogger()
    THE_LOGGER.setLevel(logging.DEBUG)
    THE_LOGGER.addHandler(LF_HANDLER)
    THE_LOGGER.addHandler(LC_HANDLER)
    THE_LOGGER.info('Deck executed as main')
    # LOGGER.setLevel(logging.DEBUG)

    try:
        main()

    except(Exception, KeyboardInterrupt) as exc:
        sys.exit(str(exc))

    finally:
        sys.exit()
