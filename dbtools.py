#!/usr/bin/env python3

"""tools for accessing the database"""
import os
import sys
import logging
import logging.handlers
import mysql.connector as mariadb

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/dbtools'

class DBTools:
    """DBTools

    """
    def __init__(self):
        self.db = mariadb.connect(
            host="localhost",
            user="dbcurtis",
            passwd="YAqGJ7brzOBDnUJnwXQT",
            database="python1")
        self.cursor = self.db.cursor()

    def __str__(self):
        return 'DBTools: str'  # '[signal: {:.5f}dBm, {}]'.format(self.dBm, self.sl)

    def __repr__(self):
        return 'DBTools: repr'  # 'SMeter: {:.5f}dBm, {}'.format(self.dBm, self.sl)

    def open(self):
        """open()

        """
        pass

    def close(self):
        """close()

        """
        self.db.commit()
        self.db.disconnect()
