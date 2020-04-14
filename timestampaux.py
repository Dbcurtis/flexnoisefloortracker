#!/usr/bin/env python3

"""This module provides some routines for handling bigint timestamps."""


from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict
import datetime
from datetime import tzinfo, timezone
from datetime import datetime as Dtc
from datetime import timedelta as Tdelta


def get_bigint_timestamp(dt: Any = None) -> int:
    # dutc: Dtc = Dtc.utcnow()
    utc: Dtc = None
    if isinstance(dt, Dtc):
        utc = Dtc.fromtimestamp(dt.timestamp())

    elif isinstance(dt, float):
        utc = Dtc.fromtimestamp(dt)
    elif 'MyTime' in str(dt.__class__):
        utc = Dtc.fromtimestamp(dt.ts)
    else:
        utc = Dtc.utcnow()

    ts1: float = (utc - Dtc(1970, 1, 1)) / Tdelta(seconds=1)
    return int(ts1 * 1000000)


def get_float_timestamp(bigint: int) -> float:
    result: float = bigint / 1000000.0
    return result
