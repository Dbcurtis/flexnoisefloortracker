#!/usr/bin/env python3

"""bandreadings.py contains code to get the get the noise floor for a particular band"""

import sys
import os
import logging
import logging.handlers
from typing import Any, Union, Tuple, Callable, TypeVar, Generic, Sequence, Mapping, List, Dict
from statistics import mean
import jsonpickle
from postproc import BANDS, BandPrams, GET_SMETER_PROTO
from flex import Flex
from smeteravg import factory, SMeterAvg
from userinput import UserInput
from smeter import SMeter
import postproc


LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/bandreadings'


# f'ZZSM{98+i*2:03};'

#def GET_BAND(wl): return math.trunc(round(wl) / 10) * 10


class Bandreadings:
    """Bandreadings(bandin: str, flexradio: Flex)

    freqsin is a list of str frequencies in the band that will be looked at
    if freqs is none, the freq will be '30100000' which will put it in the 10m band
    flex is a Flex object

    if bandid = None, the band will be determined from the freqs

    """

    def __init__(self, bandin: str, flexradio: Flex):
        self.myband: BandPrams = None

        try:
            self.myband = BANDS[bandin]
        except KeyError:
            raise

        if not self.myband.is_enabled():
            raise ValueError('Selected Band is not enabled')

        self.v: int = 4
        self.flexradio: Flex = flexradio
        self.bandid = self.myband.bandid
        self.band_signal_strength: SMeterAvg = None

    def makefreqcmd(self, a):
        return f'ZZFA{int(a) :011d};'

# signal_st = {'var': None, 'stddv': None, 'sl': None, }

    def __str__(self):
        if self.band_signal_strength:
            adBm = self.band_signal_strength.dBm.get('adBm')
            sl = self.band_signal_strength.signal_st.get('sl')
            stddv = self.band_signal_strength.signal_st.get('stddv')
            var = self.band_signal_strength.signal_st.get('var')
            return f'[band:{self.bandid}, avgsignal: {adBm :.5f}dBm, {sl}, var: {var :.5f}, stddv: {stddv :.5f}]'

        return f'no reading, band {self.bandid}'

    def __repr__(self):
        if self.band_signal_strength:
            #adBm = self.band_signal_strength.dBm.get('adBm')
            #sl = self.band_signal_strength.signal_st.get('sl')
            #stddv = self.band_signal_strength.signal_st.get('stddv')
            #var = self.band_signal_strength.signal_st.get('var')
            # return f'[Bandreadings: SMeterAvg: band:{self.bandid}, {adBm :.5f}dBm, {sl}, var: {var :.5f}, stddv: {stddv :.5f}]'
            return f'[Bandreadings: SMeterAvg: {str(self)}]'

        return f'Bandreadings: no reading, band {self.bandid}'

    def doit(self, testing: str = None) -> SMeterAvg:
        """doit()

        gets the signal strength for a particular band
        generates the smeteravg to check if the band is ok

        testing is a string for an open file that has the jsonpickle of the test data
        or None if to get the real data.  testing should be one of:
        1)'./quiet20band.json'
        2)'./noisy20band.json',
        assuming running in the testing direcotry
        """
        if not self.myband.is_enabled():
            raise ValueError('Selected Band is not enabled')

        self.get_readings(
            testing=testing)  # saved in self.band_signal_strength

        return self.band_signal_strength

    def cf_get_readings(self, testing: str = None) -> List[SMeter]:
        """cf_get_readings(tup,band)

        testing is a string that is a path to a file that contains data for testing

        returns all the SMeter objects used to take the readings

        """

        readings = []
        bs = self.band_signal_strength
        if testing is None:
            freqs = list({ssm.freq for ssm in bs.noise.get('highnoise')})
            freqs.sort()

            def findctrfreq(_f):
                print('needs to be completed')
                me = round(mean(freqs))
                return me
            centerfreq = findctrfreq(freqs)

            freqs = [f for f in range(
                centerfreq - 6000, centerfreq + 6000, 600)]
            results = []
            for freqn in freqs:
                freq: int = None
                cmd: str = self.makefreqcmd(freqn)
                retval: str = self.flexradio.do_cmd(cmd)
                if retval == '?;':
                    print(f'cmd: {cmd}, ret: {retval}')
                    raise Exception(f'illegal return {retval} for cmd: {cmd}')
                freq = int(retval[4:-1])
                # freq = int(self.flexradio.do_cmd(
                # self.makefreqcmd(freqn))[4:-1])

                # -------------
                band_sig_str_lst = self.flexradio.get_cat_data(
                    postproc.GET_FAST_DATA, freq)
                results.append(band_sig_str_lst)

            # avgres = [SMeterAvg(argin, band) for argin in results]

            [readings.extend(_) for _ in results]

            return readings

        with open(testing, 'r') as file:
            readings = [jsonpickle.decode(_) for _ in file.readlines()][0]

        return readings

    def cf_process_readings(self, junk=None) -> SMeterAvg:
        """cf_process_readings()


        readings is:?

        """
        pass
        # self.band_signal_strength
        # if self.band_signal_strength.signal_st.get('stddv') < 1.0:
        # return None

        #bs = self.band_signal_strength
        #avgresa = factory(self.band_signal_strength, bs.band)
        #badness = avgresa.badness()
        # if badness and badness < 0.334:
        # avgresb = factory(avgresa.noise.get('lownoise') +
        # avgresa.noise.get('midnoise'), bs.band)
        #self.dropped_high_noise = True
        #self.single_noise_freq = len(avgresa.get_noise_freqs()) == 1
        #self.dropped_freqs = list(avgresa.get_noise_freqs())
        # self.dropped_freqs.sort()

        # return avgresb

        #bs.usable = False
        # return bs

        # remove smeters with adBm being more than 1/2 std dev from asctime
        ### halfstd = avgresa.signal_st.get('stddv') / 2
        ##maxst = avgresa.dBm.get('adBm') + (avgresa.signal_st.get('stddv') / 2)

        ### minst = -130.0
        ##modsmlist = [_ for _ in avgresa.smlist if -130.0 < _.signal_st.get('dBm') < maxst]

        ##abgresb = SMeterAvg(modsmlist, band)
        # remvove freq of tup0
        ### modtup1 = [sm for sm in tup[1] if sm.freq != tup[0].freq]
        ##modreadings = [sm for sm in readings if sm.freq != tup[0].freq]
        ##jjj = SMeterAvg(tup[1], bs.band)
        ##kkk = SMeterAvg(modreadings, bs.band)
        ##a = 0
        # return avgresa

    # def changefreqs(self, testing=None) -> bool:
        # """changefreqs(testing=None)

        # """
        # return False
        #bs = self.band_signal_strength
        #readings = self.cf_get_readings(testing=testing)
        #bsmod = self.cf_process_readings(readings)
        #print('change freq scan')
        # if bs.usable and ((bs.dBm.get('mdBm') - bsmod.dBm.get('mdBm')) ** 2) < .3:
        #self.band_signal_strength = bsmod
        # return True
        # else:
        # print('NotImplementedError code') here
        ##raise NotImplementedError
        # return False

    def get_readings(self, testing: str = None) -> SMeterAvg:
        """get_readings(testing=None)

        testing can be a file path to an older version of SmeterAvg jsonpickle than the current SmeterAvg version

        self.band_signal_strength is updated with the SMeterAvg object

        """

        if testing is None:
            # for _freq in self.freqt:
                #acmd = None
                #ares = None
                # trimedr: str = None
                # try:
                    # cmd: str = self.makefreqcmd(_freq)
                    #acmd = cmd
                    # result: str = ''
                    # for _ in range(5):
                        #result = self.flexradio.do_cmd(cmd)
                        #ares = result
                        # if 'ZZFA' in result:
                            # break
                        # time.sleep(0.5)

                    # print(result)
                    #trimedr = result[4:-1]
                    #freq = int(trimedr)
                    ##freq = int(self.flexradio.do_cmd(cmd)[4:-1])
                    # band_sig_str_lst = self.flexradio.get_cat_data(
                        # postproc.GET_DATA, freq)
                    # self.readings.get(freq).extend(band_sig_str_lst)
                # except ValueError as ve:
                    # print(f'cmd: {acmd}, res: {ares},  trimedr: {trimedr}{ve}')
                    #raise ve

            myband: BandPrams = BANDS[self.bandid]
            proto: List[Tuple[Any, Any]] = GET_SMETER_PROTO[:]
            cmdlst: List[Tuple[Any, Any]] = []
            cmd: str = None
            for cmd in myband.get_freq_cmds():
                cmdlst.extend([(cmd, None)])
                cmdlst.extend(proto)

            cmdresult: List[Any] = self.flexradio.get_cat_dataA(cmdlst)
            sm_readings: List[SMeter] = [_ for _ in cmdresult if isinstance(_, SMeter)]
            sm_readings.sort()
            cmdresultB: List[Any] = [_ for _ in cmdresult if not isinstance(_, SMeter)]

            maplist: List[Mapping[str, float]] = [list(_.signal_st.items()) for _ in sm_readings]
            keyset: Set[str] = set([list(sm.signal_st.items())[0][1] for sm in sm_readings])

            noisedic: Dict[str, List[SMeter]] = {}
            for k in keyset:
                noisedic.setdefault(k, [])

            for ls in maplist:
                noisedic[ls[0][1]].append(ls[1][1])

            key = sorted(list(noisedic.keys()))[0]
            low_noise_readings: List[SMeter] = [sm for sm in sm_readings if sm.signal_st['sl'] == key]
            self.band_signal_strength: SMeterAvg = SMeterAvg(
                low_noise_readings, myband.bandid)

            #_rl = list(self.readings.values())
            #vals = []
            #[vals.extend(j) for j in _rl]
            #self.band_signal_strength = factory(vals, self.bandid)
            return self.band_signal_strength
        # --------------------------------
        resu = []
        with open(testing, 'r') as fl:
            resu = [jsonpickle.decode(_) for _ in fl.readlines()]

        # convert possible old version of SMeterAvg to new version
        newsmaobj = factory(resu[0])
        newsmaobj.time = resu[0].time
        self.band_signal_strength = newsmaobj
        return self.band_signal_strength

    # def savebr(self, recid):
        # """savebr(recid)

        # """
        #_s = self
        #bss = _s.band_signal_strength
        # json_of_self = f'{jsonpickle.encode(self)}\n'
        # sql = 'INSERT INTO BANDREADINGS ( \
#recid, \
#band, \
#dbm, \
#sval, \
#var, \
#stddf, \
#timedone, \
# json) Values' \
        #' ({},{},{},\'{}\',{},{},\'{}\',\'{}\');' \
        # .format(recid,
        # _s.bandid,
        # bss.dBm.get('mdBm'),
        # bss.signal_st.get('sl'),
        # bss.signal_st.get('var'),
        # bss.signal_st.get('stddv'),
        # bss.time,
        # json_of_self)

        # _CU.execute(sql)
    # _DB.commit()
        #a = 0


# class Bandreading_result:

    # def __init__(self, br: Bandreadings):
        ##freqs = freqsin if freqsin else ['30100000']
        ##self.flexradio = flexradio
        #self.freqt = br.freqt
        #self.freqi = br.freqi
        # self.v = br.v  # object version number if it exists

        # self.bandid: str = br.bandid
        #self.band_signal_strength = br.band_signal_strength
        #self.readings = br.readings
        #self.dropped_high_noise = br.dropped_high_noise
        #self.single_noise_freq = br.single_noise_freq
        #self.dropped_freqs = br.dropped_freqs
        # self._strng: str = str(br)
        # self._repr: str = repr(br)
        # pass

    # def __str__(self) -> str:
        # return self._strng

    # def __repr(self) -> str:
        # return f'Bandreading_result: {str(self)}'


def main():
    """main()

    """
    # bandrd = Bandreadings(
    # ['14000000', '14073400', '14100000', '14200000'], None)
    #bd = bandrd.bandid
    ui: UserInput = UserInput()
    ui.request(port='com4')
    flexr: Flex = Flex(ui)
    initial_state = None
    try:
        if not flexr.open():
            raise (RuntimeError('Flex not connected to serial serial port'))

        print('saving current flex state')
        initial_state = flexr.save_current_state()
        print('initializing dbg flex state')
        flexr.do_cmd_list(postproc.INITIALZE_FLEX)
        bandr = Bandreadings('20', flexr)
        print('start scanning for noise')
        bss: SMeterAvg = bandr.doit()
        if False:

            with open('banddata.json', 'w') as jso:  # jsonpickle.encode
                _ = jsonpickle.encode(bss)
                jso.write(_)

            with open('banddata.json', 'r') as jsi:
                aa = jsi.readline()
                cpybss = jsonpickle.decode(aa)

            if str(bss) != str(cpybss):
                print('bss <> cpybss')

        print('end scanning for noise')
        print(f'band noise is {bandr.band_signal_strength}')

    except RuntimeError as re:
        raise
    except Exception as e:
        #a = 0
        print(e)
        raise e

    finally:
        print('restore flex prior state')
        flexr.restore_state(initial_state)
        flexr.close()


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
    THE_LOGGER.info('bandreadings executed as main')
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
