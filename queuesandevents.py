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


CTX = mp.get_context('spawn')  # threading context

# QUEUES: Dict(str, CTX.JoinableQueue) = {
QUEUES = {
    # from data acquisition threads, received by the aggragator thread
    'dataQ': CTX.JoinableQueue(maxsize=100),
    # written to by the aggrator thread, read by the data processor which generates sql commands to dbq
    'dpQ': CTX.JoinableQueue(maxsize=100),
    # database commands generateed (usually) by the aggrator thread
    'dbQ': CTX.JoinableQueue(maxsize=100),

}

# STOP_EVENTS: Dict(str,) = {
STOP_EVENTS = {
    'acquireData': CTX.Event(),
    'trans': CTX.Event(),
    'agra': CTX.Event(),
    'dbwrite': CTX.Event(),
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
