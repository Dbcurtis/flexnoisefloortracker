#!/usr/bin/env python3.7
"""
Test file for need
"""

from multiprocessing import freeze_support
import unittest
import context
from deck import Deck
from queue import Full as QFull  # , Empty as QEmpty


class TestDeck(unittest.TestCase):
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
        #print('Deck: test01_instant -- start')
        deck: Deck = Deck(10)  # define z deck of 10
        #stra = str(deck)
        #repra = repr(deck)

        self.assertEqual('max: 10, len: 0, first: None', str(deck))
        self.assertEqual('Deck= max: 10, len: 0, deque([])', repr(deck))
        self.assertEqual(0, len(deck))
        deck.append("oneelement")
        deck.clear()
        self.assertEqual('max: 10, len: 0, first: None', str(deck))
        self.assertEqual('Deck= max: 10, len: 0, deque([])', repr(deck))
        self.assertEqual(0, len(deck))
        self.assertFalse(deck.look_left())
        self.assertFalse(deck.look_right())
        try:
            aa = deck.pop()
            self.fail('exception not thrown')
        except IndexError:
            pass

        try:
            aa = deck.popleft()
            self.fail('exception not thrown')
        except IndexError:
            pass

        try:
            aa = deck.pop()
            self.fail('exception not thrown')
        except IndexError:
            pass
        #print('Deck: test01_instant -- end')

        try:
            aa = deck.pop()
            self.fail('exception not thrown')
        except IndexError:
            pass

    def test02_appendPushPop(self):
        """test02_appendPushPop()

        """
        #print('Deck: test02_appendPushPop-- start')
        deck: Deck = Deck(10)
        deck.append(1)
        deck.append(2)
        deck.push(3)

        self.assertEqual(
            'Deck= max: 10, len: 3, deque([3, 1, 2])', repr(deck))
        self.assertEqual(3, deck.popleft())
        deck.push(3)

        self.assertEqual(
            'Deck= max: 10, len: 3, deque([3, 1, 2])', repr(deck))

        deck.append(deck.popleft())
        self.assertEqual(
            'Deck= max: 10, len: 3, deque([1, 2, 3])', repr(deck))

        deck.clear()
        self.assertEqual(
            'Deck= max: 10, len: 0, deque([])', repr(deck))
        i: int
        try:
            for i in range(11):
                deck.append(i)
            self.fail('missed full queue exception on append')
        except QFull:
            self.assertEqual(9, deck.look_right())

        deck.clear()
        self.assertEqual(
            'Deck= max: 10, len: 0, deque([])', repr(deck))
        try:
            for i in range(11):
                deck.push(i)
            self.fail('missed full queue exception on append')
        except QFull:
            self.assertEqual(0, deck.look_right())
            self.assertEqual(9, deck.look_left())
            self.assertEqual(10, len(deck))

        #print('Deck: test02_appendPushPop-- end')

    def test02_load_from_Q(self):
        """test02_load_from_Q()

        """
        #from queue import Empty as QEmpty, Full as QFull
        import multiprocessing as mp
        CTX = mp.get_context('spawn')
        dataq = CTX.JoinableQueue(maxsize=100)

        [dataq.put(x) for x in range(100)]
        deck: Deck = Deck(100)
        self.assertFalse(deck.look_left())
        self.assertFalse(deck.look_right())
        deck.load_from_Q(dataq, mark_done=True)
        self.assertEqual(0, deck.look_left())
        self.assertEqual(99, deck.look_right())
        [self.assertEqual(x, deck.popleft()) for x in range(100)]
        dataq.close()
        dataq = CTX.JoinableQueue(maxsize=100)

        [dataq.put(x) for x in range(100)]
        deck = Deck(50)
        deck.load_from_Q(dataq, mark_done=True, wait_sec=1.0)
        self.assertEqual(0, deck.look_left())
        self.assertEqual(49, deck.look_right())
        self.assertEqual(50, dataq.qsize())
        deck.clear()
        deck.load_from_Q(dataq, mark_done=True, wait_sec=1.0)
        self.assertEqual(50, deck.look_left())
        self.assertEqual(99, deck.look_right())
        self.assertEqual(0, dataq.qsize())
        dataq.close()

    def test03_loadQ(self):
        """test02_loadQ()

        """
        from queue import Empty as QEmpty, Full as QFull
        import multiprocessing as mp
        CTX = mp.get_context('spawn')
        dataq = CTX.JoinableQueue(maxsize=20)

        deck: Deck = Deck(10)
        try:
            self.assertEqual(10, deck.extend([x for x in range(10)]))
        except Exception:
            self.fail('unexpected exception')
        try:
            deck.extend([99, 100])
            self.fail('expected exception did not happen')
        except QFull as ex:
            pass

        deck = Deck(15)
        try:
            deck.extend([x for x in range(5)])
            deck.extend([x for x in range(15)])
            self.fail('expected exception did not happen')

        except QFull as ex:
            self.assertEqual(15, len(deck))
            self.assertEqual(0, deck.look_left())
            self.assertEqual(9, deck.look_right())

        self.assertEqual(0, dataq.qsize())
        self.assertEqual(15, deck.loadQ(dataq))
        self.assertEqual(0, len(deck))
        self.assertEqual(15, dataq.qsize())
        jj: int = 0

        try:
            while True:
                dataq.get(True, 0.001)
                dataq.task_done()
                jj += 1
        except QEmpty as e:
            a = 0
            pass
        self.assertEqual(0, dataq.qsize())

        deck = Deck(25)
        deck.extend([x for x in range(25)])

        try:
            deck.loadQ(dataq)
        except QFull as ex:

            self.assertEqual(5, len(deck))
            self.assertEqual(20, dataq.qsize())

        #aaa.load_from_Q(dataq, True)

        #[dataq.put(x) for x in range(100)]
        #deck = Deck(50)
        #deck.load_from_Q(dataq, mark_done=True)
        #self.assertEqual(0, deck.look_left())
        #self.assertEqual(49, deck.look_right())
        #self.assertEqual(50, dataq.qsize())
        # deck.clear()
        #deck.load_from_Q(dataq, mark_done=True)
        #self.assertEqual(50, deck.look_left())
        #self.assertEqual(99, deck.look_right())
        #self.assertEqual(0, dataq.qsize())
        dataq.close()

    def test04_GetLoad(self):
        """test02_loadQ()

        """
        #from queue import Empty as QEmpty, Full as QFull
        import multiprocessing as mp
        CTX = mp.get_context('spawn')
        dataqin = CTX.JoinableQueue(maxsize=110)
        dataqout = CTX.JoinableQueue(maxsize=210)

        #[dataqin.put(x) for x in range(100)]
        for i in range(100):
            dataqin.put(i)

        deck: Deck = Deck(110)
        self.assertEqual(100, deck.load_from_Q(
            dataqin, mark_done=False, wait_sec=1.0))

        def mkstr(a):
            return(str(a))

        deck.loadQ(dataqout, done_Q=dataqin, fn=mkstr)
        dataqin.close()

        deck1: Deck = Deck(110)
        cccc = deck1.load_from_Q(
            dataqout, mark_done=True, wait_sec=1.0)
        self.assertEqual(100, cccc)
        dataqout.close()


if __name__ == '__main__':

    freeze_support()
    unittest.main()
