#!/usr/bin/env python3.7
"""
stuff to manipulate a Deck (fancy deque)
"""
import os
import logging
import logging.handlers
import multiprocessing as mp
from collections import deque
from multiprocessing import freeze_support
from queue import Empty as QEmpty, Full as QFull

LOGGER = logging.getLogger(__name__)
LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/deck'


class Deck:

    def __init__(self, maxsize):
        self.deck = deque([])
        self.maxsize = maxsize
        self.qlen = 0
        self.tlock = mp.Lock()

    def __str__(self):
        result = ''
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

    def __len__(self):
        return self.qlen

    def _append(self, d):
        """_extend(d)

        append iterable d to deck

        """

        if self.qlen + 1 > self.maxsize:
            raise QFull
        self.deck.append(d)
        self.qlen += 1

    def extend(self, iterable):
        """extend(iterable)

        append iterable to deck while deck is locked
        """
        result = None
        with self.tlock:
            for v in iterable:
                self._append(v)
                if not result:
                    result = 0
                result += 1

        return result

    def _popleft(self):
        """_popleft()

        pops the value from the left side of the deck, if deck is empty raises IndexError
        """
        result = self.deck.popleft()
        self.qlen -= 1
        return result

    def popleft(self):
        """popleft()

        pops the value from the left side of the deck, if deck is empty raises IndexError
        while deck is locked

        """
        result = None
        with self.tlock:
            result = self._popleft()
        return result

    def pop(self):
        """pop()
        pops the value from the right side of the deck, if deck is empty raises IndexError
        while deck is locked
        """
        with self.tlock:
            result = self.deck.pop()
            self.qlen -= 1
        return result

    def append(self, d):
        """append(d)

        append d to right of deck
        """
        with self.tlock:
            self._append(d)
        return self.qlen

    def _push(self, d):
        """_push(d)

        appendleft d to deck

        """
        if self.qlen + 1 > self.maxsize:
            raise QFull
        self.deck.appendleft(d)
        self.qlen += 1

    def push(self, d):
        """push(d)

        appendleft d to deck while deck is locked
        """
        with self.tlock:
            self._push(d)
        return self.qlen

    def load_from_Q(self, inQ, mark_done=False, wait_sec=10):
        """load_from_Q(inQ, mark_done=False, wait_sec=10)

        loads the deck from the inQ and if mark_done is True, does so as each Q entry is added to the deck
        wait_sec is max amount to wait after the queue is empty.
        """
        count = 0
        with self.tlock:
            while self.qlen >= 0 and self.qlen < self.maxsize:
                if self.qlen >= self.maxsize:
                    raise QFull
                try:
                    self.deck.append(inQ.get(True, wait_sec))
                    self.qlen += 1
                    count += 1
                    if mark_done:
                        inQ.task_done()
                except QEmpty:
                    break
        return count

    def loadQ(self, outQ):
        """loadQ(outQ)

        emptys the deck into the specified queue
        rasies QFull if the queue becomes full

        """
        count = None
        with self.tlock:
            v = None
            while True:
                try:
                    v = self._popleft()
                    outQ.put(v, False)

                    if count is None:
                        count = 0
                    count += 1
                except QFull:
                    self._push(v)
                    raise QFull

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

    def look_right(self):
        """look_right()

        returns the rightmost entry but leaves it in the deck
        """
        result = None
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

    deck.append_data(1)
    deck.push_data(2)
    d = deck.pop_data()
    deck.append_data(d)

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
