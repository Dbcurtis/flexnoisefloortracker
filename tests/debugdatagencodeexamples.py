#!/usr/bin/env python3
"""
Test file for need
"""


#  code to generate a high variance band reading
#freqt = ['14000000', '14075000', '14100000', '14200000']
#freqi = [int(j) for j in freqt]
#readings = {f: [] for f in freqi}
#for freqd in freqi:
    ## ------------- go to the frequency
    #cat_cmd = 'ZZFA{:011d};'.format(freqd)
    #freq = int(self.flex.do_cmd(cat_cmd)[4:-1])  # set frequency
    ## -------------
    #band_sig_str_lst = self.flex.get_cat_data(postproc.GET_DATA, freq)
    #readings.get(freq).extend(band_sig_str_lst)

#_rl = list(readings.values())
#vals = []
#[vals.extend(j) for j in _rl]
#band_signal_strength = SMeterAvg(vals, 20)
#file = open('./badspotreading.json', 'w')

#file.write(f'{jsonpickle.encode(band_signal_strength)}\n')
#file.close()

#file = open('./badspotreading.json', 'r')
#lines = file.readlines()
#savedbss = [jsonpickle.decode(i) for i in lines][0]

#file.close()

#  code to generate the changefreqs data
#centerfreq = 14075000
#freqs = [f for f in range(centerfreq - 6000, centerfreq + 6000, 600)]
#results = []
#for freqn in freqs:
    #_freq = "{:011d}".format(freqn)
    #cat_cmd = 'ZZFA{};'.format(_freq)
    #freq = int(self.flex.do_cmd(cat_cmd)[4:-1])  # set frequency
    ## -------------
    #band_sig_str_lst = self.flex.get_cat_data(postproc.GET_FAST_DATA, freq)
    #results.append(band_sig_str_lst)
#avgres = [SMeterAvg(argin, 20) for argin in results]


#readings = []
#[readings.extend(a) for a in results]

## avg_all_readings = SMeterAvg(readings, 20)

#file = open('./focusedbadspotreading.json', 'w')

#file.write(f'{jsonpickle.encode(readings)}\n')
#file.close()

#file = open('./focusedbadspotreading.json', 'r')
#lines = file.readlines()
#savedreadings = [jsonpickle.decode(i) for i in lines][0]

# file.close()

# def _process_raw_data(rawdata, band):
    # """_process_raw_data(rawdata,band)

    # """
    #tfrq = rawdata[0:1][0]
    #sm_avr = SMeterAvg(rawdata[1:], band)
    # return (tfrq, sm_avr)

# def _recordprocdata(bandreadings_lst):
    # """_recordprocdata(bandreadings)

    # bandreadings_lst is a list of Bandreadings
    # """
    #recid = getrecid()

    # for bandreading in bandreadings_lst:
    # bandreading.savebr(recid)

    # _DB.commit()

# debug = []

#def _get_cat_data(cmd_list, freq, flexradio):
    #"""_get_cat_data(cmd_list)

    #returns a list of the raw or processed result from the radio

    #"""
    ##testdata = None
    ## if testResultList:
    ##testdata = testResultList[:]
    ## testdata.reverse()

    #results = []
    #for cmd in cmd_list:
        #if cmd[0][0:4] == 'wait':
            #delay = float(cmd[0][4:])
            #time.sleep(delay)
            #continue

        #result = flexradio.do_cmd(cmd[0])
        ## debug.append(result)
        #if cmd[1]:  # process the result if provided
            #_ = result.split(';')
            #vals = None
            #if len(_) > 2:
                #vals = [int(ss[4:]) for ss in _]
                #avg = int(round(sum(vals) / len(vals)))
                #result = 'ZZSM{:03d};'.format(avg)

            #result = cmd[1]((result, freq))
        #results.append(result)

    # return results


    ##sigs = self.band_signal_strength
    ##sm = sigs.get_out_of_var()
    #sm = tup[0]  # the bad reading
    #bettersm = tup[1]  # the better readings
    ## centerfreq = sm.freq
    #centerfreq = 14074206
    #freqs = [f for f in range(centerfreq - 6000, centerfreq + 6000, 600)]
    #results = []
    #for freqn in freqs:
        #_freq = "{:011d}".format(freqn)
        #cat_cmd = 'ZZFA{};'.format(_freq)
        #freq = int(self.flexradio.do_cmd(cat_cmd)[4:-1])  # set frequency
        ## -------------
        #band_sig_str_lst = self.flexradio.get_cat_data(postproc.GET_FAST_DATA, freq)
        #results.append(band_sig_str_lst)

    #jsons = []
    #for sm in results:
        #jsonver = jsonpickle.encode(sm)
        ## smd = jsonpickle.decode(jsonver)
        #jsons.append(jsonver)


    # need to make sure that this result is reasonable and find_band and
    # take out the peak if there is one.
    #avgres = [SMeterAvg(argin, band) for argin in results]
    #readings = []
    #[readings.extend(a) for a in results]
    #file = open('./temp.json', 'w')
    #for j in readings:
        #file.write(f'{jsonpickle.encode(j)}\n')
    #file.close()

    ##file = open('./temp.json', 'r')
    #resu = []
    #lines = file.readlines()
    #for _ in lines:
        #la = jsonpickle.decode(_)
        #resu.append(la)

    #file.close()
    #readings = resu[:]
    #print('debug code here')




    #avgresa = SMeterAvg(readings, band)
   ## if avgresa.signal_st.get('stddb'):
    #nothighavgres = []
    #if avgresa.signal_st.get('stddv') < 1.0:
        #a = 0
        #pass
    #else:
        #halfstd = avgresa.signal_st.get('stddv') / 2
        #maxst = avgresa.adBm + halfstd
        ## min = avgresa.adBm - halfstd
        #minst = -130.0
        #instd = [a for a in avgresa.smlist if minst < a.signal_st.get('dBm') < maxst]
        #abgresb = SMeterAvg(instd, band)
        #a = 0

        # for _freq in self.freqt:
            ## ------------- go to the frequency
            #freqd = int(_freq)
            #cat_cmd = 'ZZFA{:011d};'.format(freqd)
            #freq = int(self.flexradio.do_cmd(cat_cmd)[4:-1])  # set frequency
            ## -------------
            #band_sig_str_lst = self.flexradio.get_cat_data(postproc.GET_DATA, freq)
            #self.readings.get(freq).extend(band_sig_str_lst)

        #_rl = list(self.readings.values())
        #vals = []
        #[vals.extend(j) for j in _rl]
        # self.band_signal_strength = SMeterAvg(vals, self.bandid)
        #file = open('./noisy20band.json', 'w')

        #file.write(f'{jsonpickle.encode(self.band_signal_strength)}\n')
        #file.close()
        #file = open('./quiet20band.json', 'r')

        #resu = []
        #lines = file.readlines()
        #for _ in lines:
            #la = jsonpickle.decode(_)
            #resu.append(la)

        #file.close()
