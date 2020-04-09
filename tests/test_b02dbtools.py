#!/usr/bin/env python3
"""
Test file for need
"""
import os
import sys
import unittest
from datetime import datetime as Dtc
from datetime import tzinfo, timezone
import context
from dbtools import DBTools, get_bigint_timestamp


class MyTime:
    def __init__(self):
        self.ts: float = 0


class Testdbtools(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        dbt: DBTools = None
        dbname = 'python1test'
        try:
            dbt = DBTools(dbid=dbname)
            dbt.open()
            dbt.resetdb()
        except Exception as ex:
            print('unexpected exception')
            a = 0
        finally:
            dbt.close_and_disconnect()
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_a00instat(self):
        dbname = 'python1test'
        dm = DBTools(dbid=dbname)
        self.assertEqual(
            f'Schema is {dbname}, opened = False, connected = True', str(dm))
        self.assertEqual(
            f'DBTools: Schema is {dbname}, opened = False, connected = True', repr(dm))
        dm.close_and_disconnect()
        self.assertEqual(
            f'DBTools: Schema is {dbname}, opened = False, connected = False', repr(dm))
        dm.close_and_disconnect()
        dm.close_and_disconnect()

        dm = DBTools(dbid=dbname)
        try:
            self.assertTrue(dm.open())
            dm.close_and_disconnect()

        except:
            self.fail('unexpected exception')
            a = 0
        finally:
            try:
                dm.close_and_disconnect()
            except:
                self.fail('unexpected exception')

    def test_a01open(self):
        dbname = 'python1test'
        dm = DBTools(dbid=dbname)

        dm.open()
        self.assertEqual(
            f'Schema is {dbname}, opened = True, connected = True', str(dm))
        self.assertEqual(
            f'DBTools: Schema is {dbname}, opened = True, connected = True', repr(dm))
        try:
            dm.open()
            self.fail('did not cause exception on second open')
        except Exception as ex:
            self.assertEqual('database already opened', str(ex))
            a = 0
        dm.close_and_disconnect()
        self.assertEqual(
            f'Schema is {dbname}, opened = False, connected = False', str(dm))
        self.assertEqual(
            f'DBTools: Schema is {dbname}, opened = False, connected = False', repr(dm))
        try:
            dm.close_and_disconnect()
        except:
            self.fail(
                'should not have caused an exception on 2nd close_and_disconnect')

        dm.open()
        self.assertEqual(
            f'Schema is {dbname}, opened = False, connected = False', str(dm))

    def test_a02get_bigint_timestamp(self):
        fval: float = 31543384.000005
        utc: Dtc = Dtc(1971, 1, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        refts: float = utc.timestamp()
        self.assertAlmostEqual(fval, refts, places=6)
        self.assertEqual(31514584000005, get_bigint_timestamp(utc))

        pacific: Dtc = utc.astimezone()
        reftsa: float = pacific.timestamp()
        self.assertAlmostEqual(fval, reftsa, places=6)
        # bpts: int = get_bigint_timestamp(pacific)
        self.assertEqual(31514584000005, get_bigint_timestamp(pacific))

        refsb: int = get_bigint_timestamp()
        #utca = Dtc.now()
        jjj = int(Dtc.now().timestamp() * 1000000)
        val = refsb - jjj
        vala = val if val >= 0 else -val
        self.assertTrue(vala < 2)

        self.assertEqual(31514584000005, get_bigint_timestamp(fval))
        obj: MyTime = MyTime()
        obj.ts = fval
        self.assertEqual(31514584000005, get_bigint_timestamp(obj))
        a = 0

    def test_b01setandget_timeref(self):
        dbt: DBTools = None
        dbname = 'python1test'

        try:

            dbt = DBTools(dbid=dbname)
            dbt.open()
            aa: Tuple[int, float, Dtc, str] = dbt.set_timeref(cmt='testing')
            bb = dbt.get_timeref()
            self.assertEqual(aa, bb)
            idx: int = aa[0]  # 1
            self.assertEqual(1, idx)
            timestamp: float = aa[1]
            time: Dtc = aa[2]
            utc1: Dtc = Dtc.fromtimestamp(timestamp, timezone.utc)
            local: Dtc = utc1.astimezone()
            self.assertEqual(time, local)

            cmta: str = aa[3]  # 'testing'
            self.assertEqual('testing', cmta)

        except:
            self.fail('unexpected exception')
        finally:
            dbt.close_and_disconnect()


if __name__ == '__main__':
    unittest.main()
