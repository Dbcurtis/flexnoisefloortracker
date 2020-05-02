#!/usr/bin/env python3.7
"""
Test file for need
"""

from multiprocessing import freeze_support
import unittest
import context
from sequencer import Sequencer
from time import sleep as Sleep
from time import monotonic
from statistics import mean


class TestSequencer(unittest.TestCase):
    """TestDeck

    """

    def setUp(self):
        """setUp()

        """

        pass

    def tearDown(self):
        """tearDown()

        """
        pass

    @classmethod
    def setUpClass(cls):
        """setUpClass()

        """

        pass

    @classmethod
    def tearDownClass(cls):
        """tearDownClass()

        """
        pass

    def test01_instant(self):
        """test01_instant()

        """

        # sequ: Sequencer = Sequencer(0.1)  # sequencer with an interval of .1 sec
        # sequencer with an interval of 15.0 sec
        sequ: Sequencer = Sequencer(5.0)  # init for 10 sec delay
        self.assertAlmostEqual(5.0, sequ.delayseconds)
        self.assertEqual(20, len(sequ._to_do_sched))
        self.assertFalse(sequ.do_it_now())
        self.assertEqual(0, sequ.skipped)
        initiallastsched = sequ._to_do_sched[-1]
        cnt: int = 0
        starttime = monotonic()
        while not sequ.do_it_now():
            Sleep(0.25)
            self.assertEqual(0, sequ.skipped)
            cnt += 1

        endtime = monotonic()
        toloop = endtime - starttime
        self.assertAlmostEqual(5.0, round(toloop, 0))
        currentlastsched = sequ._to_do_sched[-1]
        delay1 = currentlastsched - initiallastsched
        self.assertAlmostEqual(5.0, delay1)
        self.assertEqual(20, cnt)
        sched: List[float] = list(sequ._to_do_sched)
        ll: List[float] = []
        for i in range(1, len(sched)):
            ll.append(sched[i] - sched[i - 1])

        self.assertEqual(5.0, mean(ll))

        sequ = Sequencer(1)  # init for 1 sec delay
        Sleep(10.5)
        self.assertEqual(20, len(sequ._to_do_sched))
        self.assertTrue(sequ.do_it_now())
        self.assertEqual(20, len(sequ._to_do_sched))
        self.assertEqual(10, sequ.skipped)

        sequ = Sequencer(5.0)  # init for 5 sec delay
        waittime: float = sequ.get_nxt_wait()
        Sleep(waittime - 0.5)
        waittime = sequ.get_nxt_wait()
        self.assertAlmostEqual(0.5, waittime)


if __name__ == '__main__':

    freeze_support()
    unittest.main()
