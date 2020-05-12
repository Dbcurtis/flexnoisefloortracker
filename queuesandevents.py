#!/usr/bin/env python3

"""defines some semi globals"""
from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set
import multiprocessing as mp
from queue import Empty as QEmpty, Full as QFull


CTX = mp.get_context('spawn')  # threading context

# QUEUES: Dict(str, CTX.JoinableQueue) = {
QUEUES = {
    # from data acquisition threads, received by the aggragator thread
    'dataQ': CTX.JoinableQueue(maxsize=100),
    # database commands generateed (usually) ty the aggrator thread
    'dbQ': CTX.JoinableQueue(maxsize=100),
    # written to by the aggrator thread, read by the data processor which generates sql commands to dbq
    'dpQ': CTX.JoinableQueue(maxsize=100)

}

# STOP_EVENTS: Dict(str,) = {
STOP_EVENTS = {
    'acquireData': CTX.Event(),
    'trans': CTX.Event(),
    'dbwrite': CTX.Event(),
    'agra': CTX.Event(),
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
