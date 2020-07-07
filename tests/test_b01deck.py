#!/usr/bin/env python3.7
"""
Test file for need
"""

from multiprocessing import freeze_support
import unittest
import context
from deck import Deck
# from queue import Full as QFull  # , Empty as QEmpty
from deck import DeckFullError, OutQFullError


# class DeckFullError(Error):
#"""Raise when the Deck is fulll"""

# def __init__(self, *args):
#super(DeckFullError, self).__init__(*args)


# class OutQFullError(Error):
#"""Raise when the output Q is full"""

def emptyQ(q):

    try:
        while True:
            a = q.get_nowait()
            q.task_done()
    except:
        pass


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

        deck: Deck = Deck(10)  # define z deck of 10

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
        except DeckFullError:
            self.assertEqual(9, deck.look_right())

        deck.clear()
        self.assertEqual(
            'Deck= max: 10, len: 0, deque([])', repr(deck))
        try:
            for i in range(11):
                deck.push(i)
            self.fail('missed full queue exception on append')
        except DeckFullError:
            self.assertEqual(0, deck.look_right())
            self.assertEqual(9, deck.look_left())
            self.assertEqual(10, len(deck))

        #print('Deck: test02_appendPushPop-- end')

    def test03_q2deck(self):
        """test02_q2deck()

        """
        #from queue import Empty as QEmpty, Full as QFull
        import multiprocessing as mp
        CTX = mp.get_context('spawn')
        dataq = CTX.JoinableQueue(maxsize=100)

        #
        # test that can empty a que into the deck
        #
        [dataq.put(x) for x in range(100)]
        deck: Deck = Deck(101)
        self.assertFalse(deck.look_left())
        self.assertFalse(deck.look_right())
        deck.q2deck(dataq, mark_done=True)
        self.assertEqual(100, len(deck))
        self.assertEqual(0, deck.look_left())
        self.assertEqual(99, deck.look_right())
        self.assertTrue(dataq.empty())
        [self.assertEqual(x, deck.popleft()) for x in range(100)]
        #
        # test that can load from Q and exactly fill the deck
        #
        [dataq.put(x) for x in range(100)]
        deck: Deck = Deck(100)
        try:
            deck.q2deck(dataq, mark_done=True)
        except Exception as ex:
            self.fail(f'unexpected exception {ex}')

        self.assertEqual(100, len(deck))
        self.assertEqual(0, deck.look_left())
        self.assertEqual(99, deck.look_right())
        self.assertTrue(dataq.empty())
        [self.assertEqual(x, deck.popleft()) for x in range(100)]

        # check that the deck can fill from que and raise DeckFullError
        [dataq.put(x) for x in range(100)]
        deck = Deck(50)
        try:
            deck.q2deck(dataq, mark_done=True, wait_sec=1.0)
            self.fail('DeckFullError not QFull')
        except DeckFullError as dfe:
            a = 0
            pass
        self.assertEqual(50, len(deck))
        self.assertEqual(0, deck.look_left())
        self.assertEqual(49, deck.look_right())
        self.assertEqual(50, dataq.qsize())
        deck.clear()
        deck.q2deck(dataq, mark_done=True, wait_sec=1.0)
        self.assertEqual(50, deck.look_left())
        self.assertEqual(99, deck.look_right())
        self.assertEqual(0, dataq.qsize())

        emptyQ(dataq)

        dataq.close()

    def test04_deck2q1andextend(self):
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
        except DeckFullError as ex:
            a = 0
            pass

        deck = Deck(15)
        try:
            deck.extend([x for x in range(5)])
            deck.extend([x for x in range(15)])
            self.fail('expected exception did not happen')

        except DeckFullError as ex:
            self.assertEqual(15, len(deck))
            self.assertEqual(0, deck.look_left())
            self.assertEqual(9, deck.look_right())

        self.assertEqual(0, dataq.qsize())
        self.assertEqual(15, deck.deck2q(dataq))
        self.assertEqual(0, len(deck))
        self.assertEqual(15, dataq.qsize())

        # empty dataq
        try:
            while True:
                dataq.get(True, 0.001)
                dataq.task_done()
        except QEmpty:
            pass
        self.assertEqual(0, dataq.qsize())

        deck = Deck(25)
        deck.extend([x for x in range(25)])

        try:
            deck.deck2q(dataq)
            self.fail('expected exception did not happen')
        except OutQFullError as ex:
            self.assertEqual(5, len(deck))
            self.assertEqual(20, dataq.qsize())

        # try:
            # while True:
            #aa = dataq.get_nowait()
            # dataq.task_done()
        # except Exception:
            # pass

        emptyQ(dataq)
        dataq.close()

    def test05_deck2lst(self):
        deck: Deck = Deck(50)
        for _ in range(50):
            deck.append(_)
        result: List[int] = deck.deck2lst()
        for _ in range(50):
            self.assertEqual(_, result[_])

    def test06_q2deckanddeck2q1(self):
        """test02_loadQ()

        """

        import multiprocessing as mp
        CTX = mp.get_context('spawn')
        dataqin = CTX.JoinableQueue(maxsize=100)
        dataqout_large = CTX.JoinableQueue(maxsize=102)
        dataqout_small = CTX.JoinableQueue(maxsize=10)

        [dataqin.put(x) for x in range(25)]
        # for i in range(100):
        # dataqin.put(i)

        deck: Deck = Deck(50)
        cnt: int = None
        lstint: List[int] = []
        try:
            cnt = deck.q2deck(dataqin, mark_done=True, wait_sec=0.5)
            self.assertEqual(25, cnt)
            self.assertEqual(25, len(deck))
            [dataqin.put(x) for x in range(25, 30)]
            self.assertEqual(5, dataqin.qsize())
            cnt = deck.q2deck(dataqin, mark_done=True, wait_sec=0.5)
            self.assertEqual(5, cnt)
            self.assertTrue(dataqin.empty())
            self.assertEqual(30, len(deck))
            lstint = list(deck.deck)
            self.assertEqual(30, len(lstint))
            self.assertEqual(0, lstint[0])
            self.assertEqual(29, lstint[29])

            [dataqin.put(x) for x in range(30, 100)]
            cnt = deck.q2deck(dataqin, mark_done=True, wait_sec=0.5)
            self.fail('did not generate exception')

        except DeckFullError as dfe:
            self.assertEqual(50, len(deck))
            self.assertEqual(5, cnt)
            self.assertEqual('cnt=20', dfe.args[0])
            self.assertEqual(50, dataqin.qsize())

        lstint = list(deck.deck)
        for i in range(50):
            self.assertEqual(i, lstint[i])

        # the deck is full, lets try to add more
        try:
            cnt = deck.q2deck(dataqin, mark_done=True, wait_sec=0.5)
            self.fail('did not generate exception')

        except DeckFullError as dfe:
            self.assertEqual('cnt=0', dfe.args[0])

        def mkstr(a):
            return(str(a))
        try:
            cnt = deck.deck2q(dataqout_small, fn=mkstr)
            self.fail('should have thrown an exception')
        except OutQFullError as oqfe:
            self.assertEqual('cnt=10', oqfe.args[0])

        self.assertEqual(40, len(deck))
        self.assertEqual(10, dataqout_small.qsize())
        tempdeck = Deck(20)
        cnt = tempdeck.q2deck(dataqout_small, mark_done=True)
        lstint = list(tempdeck.deck)
        self.assertEqual(0, dataqout_small.qsize())
        for i in range(10):
            self.assertEqual(str(i), lstint[i])

        # self.assertEqual(100, deck.q2deck(
            # dataqin, mark_done=False, wait_sec=1.0))

        #self.assertEqual(100, len(deck))
        # self.assertTrue(dataqin.empty())

        #deck.deck2q(dataqout, done_Q=dataqin, fn=mkstr)
        #self.assertEqual(0, len(deck))
        #self.assertEqual(100, dataqout.qsize())

        #checkdeck = Deck(110)
        # self.assertEqual(100, checkdeck.q2deck(
            # dataqout, mark_done=True, wait_sec=1.0))
        #aa: str = checkdeck.look_left()
        #self.assertEqual('0', aa)
        # self.assertTrue(dataqout.empty())

        #deck1: Deck = Deck(110)
        # cccc = deck1.q2deck(
            # dataqout, mark_done=True, wait_sec=1.0)
        #self.assertEqual(100, cccc)

        #self.fail('need to test full queue exception')

        emptyQ(dataqin)
        emptyQ(dataqout_small)
        emptyQ(dataqout_large)

        dataqin.close()
        dataqout_small.close()
        dataqout_large.close()


if __name__ == '__main__':

    freeze_support()
    unittest.main()
