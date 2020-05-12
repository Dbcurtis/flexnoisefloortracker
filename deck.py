#!/usr/bin/env python3.7
"""
stuff to manipulate a Deck (fancy deque)
"""

import os
import logging
import logging.handlers
import multiprocessing as mp
from typing import Any, Deque, Iterable
#from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set, Deque, Iterable
from collections import deque
from multiprocessing import freeze_support
from queue import Empty as QEmpty, Full as QFull


LOGGER = logging.getLogger(__name__)
LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/deck'


def _ident(a):
    return a


class Error(Exception):
    pass


class DeckFullError(Error):
    """Raise when the Deck is fulll"""

    def __init__(self, *args):
        super(DeckFullError, self).__init__(*args)


class OutQFullError(Error):
    """Raise when the output Q is full"""

    def __init__(self, *args):
        super(OutQFullError, self).__init__(*args)

class Deck:

    def __init__(self, maxsize: int):
        self.deck: Deque[Any] = deque([])  # a deque of the deck contents
        self.maxsize: int = maxsize
        self.qlen: int = 0  # number of the items in the deck
        self.tlock: mp.Lock = mp.Lock()

    def __str__(self):
        result: str = ''
        with self.tlock:
            val = None
            if self.qlen > 0:
                val = self.deck[0]
            result = (f'max: {self.maxsize}, len: {self.qlen}, first: {val}')
        return result

    def __repr__(self):
        result = ''
        with self.tlock:
            result = f'Deck= max: {self.maxsize}, len: {self.qlen}, {str(self.deck)}'
        return result

    def __len__(self) -> int:
        return self.qlen

    def _append(self, d: Iterable):
        """_extend(d)

        append iterable d to deck

        """

        if self.qlen + 1 > self.maxsize:
            raise DeckFullError
        self.deck.append(d)
        self.qlen += 1

    def extend(self, iterable: Iterable) -> int:
        """extend(iterable)

        append iterable to deck while deck is locked
        """
        result: int = None
        with self.tlock:
            for v in iterable:
                self._append(v)
                if not result:
                    result = 0
                result += 1

        return result

    def _popleft(self) -> Any:
        """_popleft()

        pops the value from the left side of the deck, if deck is empty raises IndexError
        """
        result: Any = self.deck.popleft()
        self.qlen -= 1
        return result

    def popleft(self) -> Any:
        """popleft()

        pops the value from the left side of the deck, if deck is empty raises IndexError
        while deck is locked

        """
        result: Any = None
        with self.tlock:
            result = self._popleft()
        return result

    def pop(self) -> Any:
        """pop()
        pops the value from the right side of the deck, if deck is empty raises IndexError
        while deck is locked
        """
        result: Any = None
        with self.tlock:
            result = self.deck.pop()
            self.qlen -= 1
        return result

    def append(self, d: Any) -> int:
        """append(d)

        append d to right of deck
        """
        with self.tlock:
            self._append(d)
        return self.qlen

    def _push(self, d: Any):
        """_push(d)

        appendleft d to deck

        """
        if self.qlen + 1 > self.maxsize:
            raise DeckFullError
        self.deck.appendleft(d)
        self.qlen += 1

    def push(self, d: Any) -> int:
        """push(d)

        appendleft d to deck while deck is locked
        """
        with self.tlock:
            self._push(d)
        return self.qlen

    def q2deck(self, inQ, mark_done: bool = False, wait_sec: float = 1.0, fn=_ident) -> int:
        """load_from_Q(inQ, mark_done=False, wait_sec=10, fn=_ident)

        loads the deck from the inQ and if mark_done is True, does so as each Q entry is added to the deck
        wait_sec is max amount to wait after the queue is empty.

        rases DeckFullError if deck reaches maxsize
        returns the number of items read from the queue on this invocation (Not the deck length)
        """
        count: int = 0
        with self.tlock:
            while self.qlen >= 0 and self.qlen <= self.maxsize:
                if self.qlen >= self.maxsize and not inQ.empty():
                    raise DeckFullError(f'cnt={count}')
                try:
                    self.deck.append(fn(inQ.get(True, wait_sec)))
                    self.qlen += 1
                    count += 1
                    if mark_done:
                        inQ.task_done()
                except QEmpty:
                    break
        return count

    def deck2q(self, outQ, done_Q=None, fn=_ident) -> int:
        """deck2q(outQ, done_Q=None, fn=_ident)

        emptys the deck into the specified outQ,
        if done_Q is specified, will do a task_done operation on the done_Q
        fn operates on the value being loaded(which defaults to returning the unchanged value)

        rasies OutQFullError if the queue becomes full

        """
        count: int = None
        with self.tlock:
            if self.qlen == 0:
                count = 0
            else:
                count = self._loadQ(outQ, done_Q, fn)
        return count

    def _loadQ(self, outQ, done_Q=None, fn=_ident) -> int:
        """loadQ(outQ)

        emptys the deck into the specified outQ,  If the outQ becomes full, the transfer stops, only values written to the que are
        removed from the deck and QFull is raised.  More items can be added to the Deck

        if done_Q is specified, will do a task_done operation on the done_Q
        fn operates on the value being loaded(which defaults to returning the unchanged value)

        """

        count: int = None
        v = None
        while True:
            try:
                v: Any = self._popleft()
                outQ.put(fn(v), False)
                if not done_Q is None:
                    done_Q.task_done()

                if count is None:
                    count = 0
                count += 1
            except QFull:
                self._push(v)
                raise OutQFullError(f'cnt={count}')

            except IndexError:
                break
        return count

    def look_left(self):
        """look_left()

        returns the leftmost entry but leaves it in the deck
        """
        result = None
        with self.tlock:
            if self.qlen > 0:
                result = self.deck[0]

        return result

    def look_right(self) -> Any:
        """look_right()

        returns the rightmost entry but leaves it in the deck
        """
        result: Any = None
        with self.tlock:
            if self.qlen > 0:
                result = self.deck[-1]

        return result

    def clear(self):
        """clear()

        emptys the deck

        """
        with self.tlock:
            self.deck.clear()
            self.qlen = 0
        return


def main():
    deck = Deck(10)
    print(str(deck))
    print(repr(deck))

    deck.append(1)
    deck.push(2)
    d = deck.pop()
    deck.append(d)

    print(deck)
    print(str(deck))
    print(repr(deck))

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
