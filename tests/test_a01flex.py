#!/usr/bin/env python3
"""
Test file for need
"""

import time
import unittest
from typing import List, Sequence, Dict, Mapping, Set
import context
from postproc import BANDS, BandPrams, GET_SMETER_PROTO
from userinput import UserInput
from flex import Flex
from smeter import SMeter
from smeteravg import SMeterAvg
import postproc


class Testflex(unittest.TestCase):
    """Testflex

    unit testing for the flex class

    """

    # def initialize_flex(self):
    # """initialize_flex()

    # """

    #_ui = UserInput()
    # _ui.request('com4')
    #self.flex = Flex(_ui)
    # self.flex.open()
    # self.initialize_flex()
    # self.flex.do_cmd_list(postproc.INITIALZE_FLEX)
    #results = self.flex.do_cmd_list(postproc.INITIALZE_FLEX)
    # return results

    def setUp(self):
        _ui = UserInput()
        _ui.request('com4')
        self.flex = Flex(_ui)
        self.flex.open()
        _ = self.flex.do_cmd_list(postproc.INITIALZE_FLEX)
        self.assertEqual(13, len(_))

    def tearDown(self):
        self.flex.close()

    @classmethod
    def setUpClass(cls):
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        cls.initial_state = flex.save_current_state()
        flex.close()

    @classmethod
    def tearDownClass(cls):
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)
        flex.open()
        flex.restore_state(cls.initial_state)
        flex.close()

    def test01_instantiate(self):
        """test_instantiate()

        check if Flex instiantiates and has expected str and repr without flex being opened

        """
        _ui = UserInput()
        _ui.request('com4')
        flex = Flex(_ui)

        self.assertEqual('Flex cat: com4, opened: False', str(flex))
        self.assertEqual('[Flex] Flex cat: com4, opened: False', repr(flex))
        flex.close()

    def test02_open_close(self):
        """test_open_close()

        check if Flex instiantiates and opens and has expected str and repr flex
        verifies that flex closes
        verifies re-open and can do a simple do_cmd
        """

        self.assertEqual('Flex cat: com4, opened: True', str(self.flex))
        self.assertEqual(
            '[Flex] Flex cat: com4, opened: True', repr(self.flex))

        self.flex.close()
        self.assertEqual('Flex cat: com4, opened: False', str(self.flex))
        self.assertEqual(
            '[Flex] Flex cat: com4, opened: False', repr(self.flex))

        self.flex.open()
        result = self.flex.do_cmd('ZZIF;')
        self.assertEqual(41, len(result))

    def test03_do_cmd(self):
        """test_do_cmd()

        checks error conditions on do_cmd
        """
        result = self.flex.do_cmd('ZZIF;')

        self.assertEqual(41, len(result))
        result = self.flex.do_cmd('ZZIF')
        self.assertEqual(41, len(result))
        result = self.flex.do_cmd('')
        self.assertEqual('??;', result)
        result = self.flex.do_cmd('junk')
        self.assertEqual('??;', result)

    def test04_save_current_state(self):
        """test_save_current_state()

        checks that flex state can be saved, modified and restored

        """

        savedstate = self.flex.save_current_state()
        self.assertEqual(savedstate, self.flex.saved_state[:])

        self.flex.restore_saved_state()
        newsavedstate = self.flex.save_current_state()
        self.assertEqual(savedstate, newsavedstate)

        _aa = int([i for i in newsavedstate if 'ZZFA' in i][0][-12:-1])
        _aa = 14000000 if _aa != 14000000 else 15000000
        # aat = f'ZZFA{_aa:011};'

        self.flex.do_cmd(f'ZZFA{_aa:011};')
        modstate = self.flex.save_current_state()
        self.assertNotEqual(modstate, newsavedstate)

        restore_results = self.flex.restore_state(newsavedstate)
        self.assertEqual(19, len(restore_results))
        self.assertEqual(newsavedstate, self.flex.saved_state)

    def test10_get_cat_data(self):
        """testget_cat_data()
        """
        gdata1 = [
            ('wait0.5', None, ),
            ('ZZIF;', postproc.zzifpost, ),
        ]

        stime = time.perf_counter()
        results = self.flex.get_cat_data([], 14_000_000)
        etime = time.perf_counter()
        dtime = etime - stime
        self.assertAlmostEqual(0.00, dtime, delta=0.001)

        stime = time.perf_counter()
        results = self.flex.get_cat_data([('wait0.5', None, ), ], 14_000_000)
        etime = time.perf_counter()
        dtime = etime - stime
        self.assertAlmostEqual(0.50, dtime, delta=0.1)

        results = self.flex.get_cat_data(gdata1, 14_000_000)
        dtime = etime - stime
        self.assertAlmostEqual(0.50, dtime, delta=0.1)
        self.assertEqual(1, len(results))

    def test05_jsonpickel(self):
        import jsonpickle
        try:
            self.flex.close()
            jsonpickelst = jsonpickle.encode(
                self.flex)  # _ui cannot be pickeled
            testob = jsonpickle.decode(jsonpickelst)
            rp1 = repr(self.flex)
            rp2 = repr(testob)
            self.assertEqual(rp1, rp2)
        except Exception as ex:
            self.fail("unexpected exception")
            a = 0
            b = 0

    def test11_get_cat_dataA(self):
        myband: BandPrams = BANDS['20']

        proto: List[Tuple[Any, Any]] = GET_SMETER_PROTO[:]
        cmdlst: List[Tuple[Any, Any]] = []
        for cmd in myband.get_freq_cmds():
            cmdlst.extend([(cmd, None)])
            cmdlst.extend(proto)

        cmdresult: List[Any] = self.flex.get_cat_dataA(cmdlst)
        sm_readings: List[SMeter] = [_ for _ in cmdresult if isinstance(_, SMeter)]
        sm_readings.sort()

        cmdresultB: List[Any] = [_ for _ in cmdresult if not isinstance(_, SMeter)]
        cmdrestup = tuple(cmdresultB)
        self.assertEqual(myband.get_freq_cmds(), cmdrestup)

        maplist: List[Mapping[str, float]] = [list(_.signal_st.items()) for _ in sm_readings]
        keyset: Set[str] = set([list(sm.signal_st.items())[0][1] for sm in sm_readings])

        noisedic: Dict[str, List[SMeter]] = {}
        for k in keyset:
            noisedic.setdefault(k, [])

        for ls in maplist:
            noisedic[ls[0][1]].append(ls[1][1])

        key = sorted(list(noisedic.keys()))[0]
        dkdk: List[SMeter] = [sm for sm in sm_readings if sm.signal_st['sl'] == key]

        sma: SMeterAvg = SMeterAvg(dkdk, myband.bandid)
        a = 0


if __name__ == '__main__':
    unittest.main()
