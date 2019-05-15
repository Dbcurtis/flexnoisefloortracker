#!/usr/bin/env python3
""" Module for interfacing to the serial handlers """

import os
import logging
import logging.handlers
import serial

LOGGER = logging.getLogger(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/logs'
LOG_FILE = '/myserial'

class MySerial(serial.Serial):  # pylint: disable=too-many-ancestors
    """MySerial(controller_info)

    controller_info is ***?
    """
    _debugging = False

    _debugreturns = [b'ok\nDTMF>']
    _dbidx = 0
    _NO = -1


    """Byte_2_String(bs)

    Takes a byte array (bs) and returns the corrosponding string
    """
    def Byte_2_String(bs): return "".join([chr(int(b)) for b in bs if int(b) != 13])

    String_2_Byte = lambda st: bytes([ord(s) for s in st])
    """String_2_Byte(st)

    Takes a string (st) and returns a corrosponding byte array
    """
    def String_2_Byte(st): return bytes([ord(s) for s in st])

    def __init__(self, controller_info):
        super(MySerial, self).__init__()
        self.controller_info = controller_info
        self.cont_prompt = self.controller_info.newcmd_dict.get('prompt')

    def __str__(self):
        #_aa = super(MySerial, self).__str__()
        return "testing:" + str(MySerial._debugging) + ", " + super(MySerial, self).__str__()


    def dread(self, numchar):
        """dread(numchar)


        """
        if not MySerial._debugging:
            return self.read(numchar)

        if MySerial._dbidx < 0:
            return  [b'OK\nDTMF>']
        result = MySerial._debugreturns[MySerial._dbidx]
        MySerial._dbidx += 1
        return result

    def sp_ok(self):  # assume the sp is open
        """spOK()

        Checks to see if an open serial port is communicating with the controller

        Writes a \r to the serial port and reads the result
        If the result ends with the controller prompt (i.e. DTMF>)
        the port and repeater are communicating

        Returns True if communicating, False if not
        """
        _sp = self
        _sp.flushInput()
        _sp.close()
        _to = _sp.timeout
        _sp.timeout = 0.25 + (110.0/_sp.baudrate)
        _sp.open()
        _sp.dread(9999)
        _sp.write(MySerial.String_2_Byte('\r'))
        #will generate some response
        #ending in DTMF> if the cps rate is correct (for controllers like the dlxii)

        ctrlresult = MySerial.Byte_2_String(_sp.dread(9999))
        _sp.close()
        _sp.timeout = _to
        _sp.open()
        return ctrlresult.endswith(self.cont_prompt)

    def find_baud_rate(self):
        """find_baud_rate()

        Attempts to communicate to the repeater controller using speeds
        9600,19200,4800,1200,600,300.
        The first attempt that works (see spOK) will be selected to be the
        speed for the serial port.
        There is some attempt to adjust the wait serial port timeouts
        responsive to the baud rate.
        My current belief is that the wait is not that importaint, but have
        not yet tried anything other than 9600

        If the baud rate cannot be determined, the sp is returned to
        the state it was on entry.

        side-effects
        If the serial port is open on entry, it will be open on exit,
        otherwise it is closed.

        returns True if a matching baud rate is found, otherwise returns False
        """
        _sp = self
        _ci = self.controller_info

        is_open = _sp.isOpen()
        if not is_open:
            _sp.open()

    #  if spOpen:  # if open port, and it is communicating just return the baudrate
        if self.sp_ok():
            if not is_open:
                _sp.close()
            return True
        _sp.flushInput()
        _sp.close()  # if open and not communicating the port is closed

        savedbr = _sp.baudrate
        savedto = _sp.timeout

        scps = MySerial._NO  # setup for storing the selected baud rate and timeout
        sto = 0.0
        # at this point the serial port is always closed
        for cpsd in _ci.cps_data:
            _sp.baudrate = cpsd.bps
            _sp.timeout = cpsd.cpsDelay
            cnt = 2
            print("trying " + str(cpsd.bps) + " baud")
            while cnt > 0:
                #  print("acnt: "+str(cnt)+", "+str(sp))
                _sp.open()  # try these settings
                if not self.sp_ok():
                    cnt = cnt - 1
                    _sp.close()
                else:
                    scps = cpsd.bps  # setting worked, so save and break the loop
                    sto = cpsd.cpsDelay
                    #print("found one");
                    #print(str(sp))
                    _sp.close()
                    cnt = -10
                    break

            if cnt < -9:
                break

        #print("scps: "+str(scps));
        if _sp.isOpen():
            _sp.close()  # close the serial port if still open

        result = False
        if scps == MySerial._NO:
            _sp.baudrate = savedbr  # no match found, just restore port
            _sp.timeout = savedto
            result = False  # show fail
        else:
            _sp.baudrate = scps  # match found, set the baud rate and timeout
            _sp.timeout = sto
            result = True  # show ok

        if is_open:  # restore the open closed state; port is currently closed
            _sp.open()
            _sp.flushInput()
        return result

if __name__ == '__main__':
    pass
