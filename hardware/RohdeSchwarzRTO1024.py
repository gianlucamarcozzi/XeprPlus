# -*- coding: utf-8 -*-
# Written by Gianluca Marcozzi g.marcozzi@fu-berlin.de
# 2024-12-05

import numpy as np
import pyvisa as visa
from time import sleep

class RohdeSchwarzRTO1024:
    def __init__(self, address):
        self._address = address
        self.rm = visa.ResourceManager()
        # print(self.rm.list_resources())
        try:
            self._connection = self.rm.open_resource(self._address)
        except:
            print('Error connecting RohdeSchwarzRTO1024\n')
            
        self.model = self._connection.query('*IDN?').split(',')[1]
        print('Connected to oscilloscope: {}.'.format(self.model))
        self._command_wait('*CLS')
        self._command_wait('*RST')
        return
    
    def disconnect(self):
        self.rm.close()
        return
        
    def _command_wait(self, command_str):
        """
        Writes the command in command_str via ressource manager and waits until
        the device has finished processing it.
        @param command_str: The command to be written
        """
        self._connection.write(command_str)
        self._connection.write('*WAI')
        while int(float(self._connection.query('*OPC?'))) != 1:
            sleep(0.02)
        return
    
    def get_xy_values(self, channel, format_type=list):
        # Return x and y data that are passed in ASCii
        # Set data format
        self._command_wait('FORM:DATA ASCii')
        
        # Do not include the x-values in the data. They will be constructed
        # from the header
        self._command_wait('EXP:WAV:INCX OFF')
        
        # Get y as string and transform to list of strings
        yraw = self._connection.query('CHAN%u:DATA:VALUES?' % channel)
        y = yraw.split('\n')[0]
        y = y.split(',')
        y = [float(elem) for elem in y]
        
        # Get header and build the x axis list
        head = self._connection.query('CHAN%u:DATA:HEADER?' % channel)
        head = head.split(',')
        head = [float(elem) for elem in head]
        x = [elem for elem in np.linspace(head[0], head[1], int(head[2]))]
        
        if format_type == 'nparray':
            x = np.array(x)
            y = np.array(y)
        
        return x, y 
        
    def enable_channels(self, channels):
        for ch in channels:
            self._command_wait('CHAN{} ON'.format(str(ch)))
            self._command_wait('CHAN{}:COUP DC'.format(str(ch)))  # DC 50Ohm
        for ch in range(1, 4):
            if ch not in channels:
                self._command_wait('CHAN{} OFF'.format(str(ch)))
        new_par = []
        new_par.append(self._connection.query('CHAN?'))
        return new_par
        
    def save(self, filename):
        savename = "C:\\Users\\Public\\files\\gianluca\\" + filename
        self._command_wait('EXP:WAV:FAST ON')
        self._command_wait('EXP:WAV:MULT ON')
        self._command_wait('RUNSingle')
        self._command_wait('CHAN1:EXP ON')
        self._command_wait('CHAN2:EXP ON')
        self._command_wait("EXP:WAV:NAME '" + savename + ".csv'")
        # print(self._connection.query("EXP:WAV:NAME?"))
        self._command_wait("MMEM:DEL '" + savename + ".*'")
        self._command_wait("EXP:WAV:SAVE")
        
        return
    
    
    def set_acquisition_type(self, acq):
        # Only possibilities: cont for run continous, single for run single
        if acq == 'cont':
            self._command_wait('RUNC')
        elif acq == 'single':
            self._command_wait('RUNS')
        else:
            print("set_acquisition_type param should be 'cont' or 'single'")
        return
        
    def set_trigger(self, source_channel=None, level=None, slope=None):
        # source_channel: 'CHAN1', 'CHAN2', 'CHAN2', 'CHAN4', 'EXT'
        if source_channel is not None:
            self._command_wait('TRIG1:SOUR {0}'.format(source_channel.upper()))
            # new_par = self._connection.query('TRIG1:SOUR?')
        if level is not None:
            if source_channel == "EXT":
                trig_n = 5
            else:
                trig_n = source_channel[-1]  # 1, 2, 3, 4
            self._command_wait('TRIG1:LEV{0} {1}'.format(
                                str(trig_n), str(level)))
            # new_par = self._connection.query(
            #     'TRIG1:LEV{}?'.format(str(source_channel)))
        if slope is not None:
            self._command_wait('TRIG1:EDGE:SLOP {}'.format(slope))
            # new_par = self._connection.query('TRIG1:EDGE:SLOP?')
                
        self._command_wait('TRIG1:ANED:COUP DC')  # DC 50Ohm
        return
        
    def set_average(self, chs, counts):
        for ch in chs:
            self._command_wait('CHAN{}:ARIT AVER'.format(ch))
        self._command_wait('ACQ:COUN {}'.format(round(counts)))
        return
        
    def set_timebase_scale(self, scale, offset):
        
        self._command_wait('TIM:SCAL {}'.format(scale))
        new_scale = self._connection.query('TIM:SCAL?')
        self._command_wait('TIM:HOR:POS {}'.format(offset))
        new_offset = self._connection.query('TIM:HOR:POS?')
        
        return new_scale, new_offset
        
    def set_resolution(self, res):
        self._command_wait('ACQ:RES {}'.format(res))
        new_par = self._connection.query('ACQ:RES?')
        return new_par
        
    def set_yaxis(self, scale1, offset1, scale2, offset2):
        self._command_wait('CHAN1:SCAL {}'.format(scale1))
        self._command_wait('CHAN1:OFFS {}'.format(offset1))
        self._command_wait('CHAN2:SCAL {}'.format(scale2))      
        self._command_wait('CHAN2:OFFS {}'.format(offset2))          
        
