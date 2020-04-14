#!/usr/bin/env python3

"""defines classes of objects that are sent over the Queues"""

#import sys
import os
#import concurrent.futures
from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict, Set

#from queue import Empty as QEmpty, Full as QFull


import logging
import logging.handlers
#import multiprocessing as mp

#from trackermain import CTX, QUEUES
from datetime import datetime as DateTime
#from collections import deque

#from deck import Deck

#import threading
#import userinput
#import flex
#from flex import Flex
#from noisefloor import Noisefloor


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/qdatainfo'


class Qdatainfo:
    def __init__(self, content: Any):
        self.content: Any = content
        self.utctime: DateTime = DateTime.now()

        pass

    def __str__(self):
        return f"t: { self.utctime.ctime()}, c: {str(self.content)}"

    def __repr__(self):
        return f'Qdatainfo: {str(self)}'

    def get(self) -> Any:
        return self.content


"""The data queues are:
    'dataQ': CTX.JoinableQueue(maxsize=100),
    # database commands generateed (usually) ty the aggrator thread
    'dbQ': CTX.JoinableQueue(maxsize=100),
    # written to by the aggrator thread, read by the data processor which generates sql commands to dbq
    'dpQ': CTX.JoinableQueue(maxsize=100)
"""


class DataQ(Qdatainfo):
    def __init__(self, content: any):
        super().__init__(content)

        pass

    def __str__(self):
        return f'{super().__str__()}'

    def __repr__(self):
        return f'DataQ: {super().__str__()}'


class LWQ(DataQ):
    #from localweather import LocalWeather

    def __init__(self, content: Any):
        super().__init__(content)

    def __str__(self):
        return f'{super().__str__()}'

    def __repr__(self):
        return f'LWQ: {super().__str__()}'

    def get(self):
        return self.content


class NFQ(DataQ):
    """NFQ(content:List[Bandreadings])


    """
    #from smeteravg import SMeterAvg
    from nfresult import NFResult

    def __init__(self, content: NFResult):
        super().__init__(content)

    def __str__(self):
        return f'{super().__str__()}'

    def __repr__(self):
        return f'NFQ: {super().__str__()}'

    def get(self) -> List[NFResult]:
        """get()

        returns the NFResult
        """
        return self.content


class DbQ(Qdatainfo):

    def __init__(self, content: any):
        super().__init__(content)
        pass

    def __str__(self):
        return f'{super().__str__()}'

    def __repr__(self):
        return f'DbQ: {super().__str__()}'


class DpQ(Qdatainfo):
    def __init__(self, content: any):
        super().__init__(content)
        pass

    def __str__(self):
        return f'{super().__str__()}'

    def __repr__(self):
        return f'DpQ: {super().__str__()}'


def main():
    pass


if __name__ == '__main__':
    #import trackermain
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
    LC_FORMATTER = logging.Formatter('%(name)s: %(levelname)s - %(message)s')
    LC_HANDLER.setFormatter(LC_FORMATTER)
    LF_HANDLER.setFormatter(LF_FORMATTER)
    THE_LOGGER = logging.getLogger()
    THE_LOGGER.setLevel(logging.DEBUG)
    THE_LOGGER.addHandler(LF_HANDLER)
    THE_LOGGER.addHandler(LC_HANDLER)
    THE_LOGGER.info('qdateinfo executed as main')
    # LOGGER.setLevel(logging.DEBUG)

    try:
        main()
        normalexit = True
    except(Exception, KeyboardInterrupt) as exc:
        print(exc)
        normalexit = False

    finally:
        if normalexit:
            sys.exit('normal exit')
        else:
            sys.exit('error exit')
