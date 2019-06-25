#!/usr/bin/env python3

"""tools for accessing the database"""
import os
import logging
import logging.handlers
import mysql.connector as mariadb
import datetime

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/dbtools'


class DBTools:
    """DBTools

    """

    def __init__(self):
        self.dbid = "python1"
        self.dbase = mariadb.connect(
            host="localhost",
            user="dbcurtis",
            passwd="YAqGJ7brzOBDnUJnwXQT",
            database=self.dbid)
        self.cursor = self.dbase.cursor()
        self.opened = False
        self.connected = True

    def __str__(self):
        return f'Schema is {self.dbid}, opened = {self.opened}, connected = {self.connected}'

    def __repr__(self):
        return f'DBTools: Schema is {self.dbid}, opened = {self.opened}, connected = {self.connected}'

    def open(self):
        """open()

        """
        self.opened = self.connected and True

    def close(self):
        """close()

        """
        if self.opened:
            self.dbase.commit()
            self.dbase.disconnect()
            self.connected = False
            self.opened = False
        elif self.connected:
            self.dbase.disconnect()
            self.connected = False

    def getrecid(self):
        """getrecid()

        """
        date_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO TIMES(timescol) Values (\"{}\");'.format(date_string)
        self.cursor.execute(sql)
        self.dbase.commit()
        self.cursor.execute('SELECT RECID FROM TIMES ORDER BY RECID DESC LIMIT 1;')
        records = self.cursor.fetchall()
        return records[0][0]


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
    THE_LOGGER.info('deleteme executed as main')
    # LOGGER.setLevel(logging.DEBUG)

    try:
        main()

    except(Exception, KeyboardInterrupt) as exc:
        sys.exit(str(exc))

    finally:
        sys.exit('normal exit')
