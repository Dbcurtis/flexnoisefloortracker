#!/usr/bin/env python3

"""defines some semi globals


Operation/dataflow
processes stopped by the acquireData event feed the dataQ

dataQ is read by thread stopped by trans event, minimal processing performed and data is writen to dpQ

dpQ is read by thread stopped by agra which generates the sql code that is written to dbQ

dbQ is read by thread stopped by dbwrite which performs the sql operations


"""
from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set
import multiprocessing as mp
from queue import Empty as QEmpty, Full as QFull
from collections import deque, namedtuple


CTX = mp.get_context('spawn')  # threading context
#BARRIER: CTX.Barrier = CTX.Barrier(1)
# BARRIER.reset()

Queuekeys = namedtuple('Queuekeys', ['dQ', 'dpQ', 'dbQ'])
QUEUE_KEYS = Queuekeys('dataQ', 'dpQ', 'dbQ')

# QUEUES: Dict(str, CTX.JoinableQueue) = {
QUEUES = {
    # from data acquisition threads, received by the aggragator thread
    QUEUE_KEYS.dQ: CTX.JoinableQueue(maxsize=100),
    # written to by the aggrator thread, read by the data processor which generates sql commands to dbq
    QUEUE_KEYS.dpQ: CTX.JoinableQueue(maxsize=100),
    # database commands generateed (usually) by the aggrator thread
    QUEUE_KEYS.dbQ: CTX.JoinableQueue(maxsize=100),

}


Stopeventkeys = namedtuple('Stopeventkeys', ['ad', 't', 'da', 'db'])

STOP_EVENT_KEYS = Stopeventkeys(
    'acquireData',
    'trans',
    'agra',
    'dbwrite')

STOP_EVENTS = {
    STOP_EVENT_KEYS.ad: CTX.Event(),
    STOP_EVENT_KEYS.t: CTX.Event(),
    STOP_EVENT_KEYS.da: CTX.Event(),
    STOP_EVENT_KEYS.db: CTX.Event(),
}


def RESET_STOP_EVENTS():
    for v in STOP_EVENTS.values():
        v.clear()


def RESET_QS():
    """RESET_QS()

    empties all the queues, marks task_done as each is removed.
    """
    for _ in QUEUES.values():
        try:
            while True:
                _.get_nowait()
                _.task_done()
        except QEmpty:
            continue


POSSIBLE_F_KEYS: List[str] = [
    'weather',
    'noise',
    'transfer',
    'dataagragator',
    'dbwriter'
]
Futurekeys = namedtuple('Futurekeys', [
    'w',
    'n',
    't',
    'da',
    'db'])

POSSIBLE_F_TKEYS = Futurekeys('weather',
                              'noise',
                              'transfer',
                              'dataagragator',
                              'dbwriter')

Enables = namedtuple('Enables', Futurekeys._fields)

Argkeys = namedtuple('Argkeys', Futurekeys._fields)
ARG_KEYS = Argkeys(0, 1, 2, 3, 4)

