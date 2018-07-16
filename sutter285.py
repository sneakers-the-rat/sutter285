# sutterMP285 : A python class for using the Sutter MP-285 positioner
# 
# SUTTERMP285 implements a class for working with a Sutter MP-285
#   micro-positioner. The Sutter must be connected with a Serial
#   cable. 
#
# This class uses the python "serial" package which allows for 
#   with serial devices through 'write' and 'read'. 
#   The communication properties (BaudRate, Terminator, etc.) are 
#   set when invoking the serial object with serial.Serial(..) (l105, 
#   see Sutter Reference manual p23).
#
# Methods:
#   Create the object. The object is opened with serial.Serial and the connection
#     is tested to verify that the Sutter is responding.
#       obj = sutterMP285()
#
#   Update the position display on the instrument panel (VFD)
#       updatePanel()
#
#   Get the status information (step multiplier, velocity, resolution)
#       [stepmult, currentVelocity, vScaleFactor] = getStatus()
#
#   Get the current absolute position in um
#       xyz_um = getPosition()
#
#   Set the move velocity in steps/sec. vScaleFactor = 10|50 (default 10).
#       setVelocity(velocity, vScaleFactor)
#
#   Move to a specified position in um [x y z]. Returns the elapsed time
#     for the move (command sent and acknowledged) in seconds.
#       moveTime = gotoPosition(xyz)
#
#   Set the current position to be the new origin (0,0,0)
#       setOrigin()
#
#   Reset the instrument
#       sendReset()
#
#   Close the connetion 
#       __del__()
#
# Properties:
#   verbose - The level of messages displayed (0 or 1). Default 1.
#
#
# Example:
#
# >> import serial
# >> from sutterMP285_1 import *
# >> sutter = sutterMP285()
#   Serial<id=0x4548370, open=True>(port='COM1', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=30, xonxoff=False, rtscts=False, dsrdtr=False)
#   sutterMP285: get status info
#   (64, 0, 2, 4, 7, 0, 99, 0, 99, 0, 20, 0, 136, 19, 1, 120, 112, 23, 16, 39, 80, 0, 0, 0, 25, 0, 4, 0, 200, 0, 84, 1)
#   step_mul (usteps/um): 25
#   xspeed" [velocity] (usteps/sec): 200
#   velocity scale factor (usteps/step): 10
#   sutterMP285 ready
# >> pos = sutter.getPosition()
#   sutterMP285 : Stage position
#   X: 3258.64 um
#   Y: 5561.32 um
#   Z: 12482.5 um
# >> posnew = (pos[0]+10.,pos[1]+10.,pos[2]+10.)
# >> sutter.gotoPosition(posnew)
#   sutterMP285: Sutter move completed in (0.24 sec)
# >> status = sutter.getStatus()
#   sutterMP285: get status info
#   (64, 0, 2, 4, 7, 0, 99, 0, 99, 0, 20, 0, 136, 19, 1, 120, 112, 23, 16, 39, 80, 0, 0, 0, 25, 0, 4, 0, 200, 0, 84, 1)
#   step_mul (usteps/um): 25
#   xspeed" [velocity] (usteps/sec): 200
#   velocity scale factor (usteps/step): 10
# >> del sutter
#
#

import serial
import struct
import time
from datetime import datetime
import sys
import numpy as np
import os
import csv


class Sutter(object):
    connected = None
    manipulator = None
    position = None
    stepmult = None
    ser = None
    log = None
    log_fields = ['event', 'position', 'timestamp']

    def __init__(self,port="COM5", timeout=5, stepmult=16, logfile = None):
        try:
            self.ser = serial.Serial(port=port,baudrate=128000,
                bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE, timeout=timeout)
            self.connected = 1
            # print(self.ser)
        except serial.SerialException:
            print 'No connection to Sutter MP-285 could be established!'
            sys.exit(1)

        # make logfile
        if isinstance(logfile, basestring):
            self.log = logfile

            # check if exists to avoid overwriting
            if os.path.exists(self.log):
                print('Logfile {} already exists! Overwrite?\n')
                yesno = raw_input('overwrite (y/n) >')
                if yesno == 'y':
                    print('Overwriting...\n')
                    # alright u said so
                    pass
                else:
                    new_path = raw_input('input new path: ')
                    self.log = new_path

            # create file
            with open(self.log, 'w') as logf:
                writer = csv.writer(logf)
                writer.writerow(self.log_fields)
                
                # log start time
                writer.writerow(['start', None, self.timestamp()])

        else:
            Warning('No logfile passed, or logfile not a string! Not logging!')

        

        self.manipulator = None
        self.position = None
        self.stepmult=stepmult
        self.get_position()

    def __del__(self):
        self.ser.close()
        print('Connection to Sutter MP-285 closed')

    def get_position(self):
        self.ser.write('C')
        msg = self.ser.readline()

        # msg will be Dxxxxyyyyzzzz\r, where D is the device
        # so want 1:13 for position
        self.position = np.array(struct.unpack('lll', msg[1:13])) / self.stepmult
        #self.position = self.decode_position(msg[1:])
        print("{} - Current position: X = {}, Y = {}, Z = {}".format(self.timestamp(), self.position[0],
                                                                     self.position[1], self.position[2]))
        
        # log
        with open(self.log, 'ab') as logf:
            writer = csv.writer(logf)
            writer.writerow(['get_pos', self.position, self.timestamp()])

    def set_position(self, pos):
        # pos is an x, y, z tuple in microns.
        # multiply by step multiplier to convert to stepper units, then pack into bytes
        pos_stepper = struct.pack('lll', int(pos[0] * self.stepmult), int(pos[1] * self.stepmult), int(pos[2] * self.stepmult))
        self.ser.write('M'+pos_stepper)

        print('{} - Moving to X = {}, Y = {}, Z = {}'.format(self.timestamp(), pos[0],
                                                             pos[1], pos[2]))
        
        # log move
        with open(self.log, 'ab') as logf:
            writer = csv.writer(logf)
            writer.writerow(['set_pos', np.array(pos), self.timestamp()])

        # flush any latent carriage returns
        moved = self.ser.readline()
        #while moved == '\r':
        #    moved = self.ser.read()

        # self.get_position()

    def get_active_manipulator(self):
        self.ser.write("K")
        msg = self.ser.readline()

        # manipulator number is first hex byte
        self.manipulator = ord(msg[0])

    def set_active_manipulator(self, manipulator):
        pass
        # not implementing now
        #manip_hex = struct.pack('1h', int(manipulator))



    def read_serial(self):
        # continue to read until carriage return
        # sorta deprecated, but keeping around just in case
        message = []
        while True:
            input = self.ser.read()
            if input == '\r':
                break
            else:
                message.append(input.encode('hex'))
        return message


    def timestamp(self):
        return datetime.now().strftime("%m-%d-%H:%M:%S.%f")[:-3]



    