#! /usr/bin/env python3
#coding: utf8
# TODO Change this to a class (?) 

#import lirc
#import time
import os
import sys
import spidev
import smbus
##import config
import threading
from evdev import InputDevice, categorize, ecodes
import selectors
from threading import Thread, Event
import asyncio
from queue import Queue
from time import*

btnVolUp =  'KEY_VOLUMEUP' #2075 #"vol-up"  # 0x1B
btnVolDwn = 'KEY_VOLUMEDOWN' #2076 #"vol-dwn"  # 0x1C
btnSrcUp =  'KEY_NEXT' #2071 #"next"  # 0x17
btnSrcDwn = 'KEY_PREVIOUS' #2072 #"prev"  # 0x18

digitalInputs = ["SPDIF 1", "SPDIF 2", "OPTICAL 1",
            "OPTICAL 2", "AES", "OPT 2", "DIG", "USB", " "]

analogInputs = ["BAL 1", "BAL 2", "LINE 1", "LINE 2",
            "LINE 3", "LINE 4", "LINE 5"]

volTable = [2, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 76,
            80, 84, 88, 92, 94, 96, 98, 100, 102, 104, 106, 108, 
            110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 
            132, 134, 136, 138, 140, 142, 144, 146, 148, 150, 152, 
            154, 156, 158, 160, 162, 163, 164, 165, 166, 167, 168, 
            169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 
            180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 
            191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 
            202, 203, 204, 205, 206, 207, 208, 209, 210]


curInput = 0  # What Source Input are we currently at
remCode = ''  # Current remote code with toggle bit masked off
curVol = curVolLeft = curVolRight = 0
old_vol = dbVol = 0
volStep = 1
volMax = len(volTable) - 1  # PGA2320 range is 0-255 but we'll use a 0-100 lookup table

try:
    i2c_port_num = 1
    pcf_address = 0x3B  #temp address was 0x38 from 0x3B PCF8574A: A0=H, A1=H, A2=L
    analogInput = smbus.SMBus(1)
    analogInput.write_byte(pcf_address, 0x00) # Set PCF8574A to all outputs
except:
    print("Could not connect to the PCF8574")


# Open SPI bus instance for PGA2320
try:
    SPI_PORT = 1
    SPI_DEVICE = 0
    pga2320 = spidev.SpiDev()
    pga2320.open(SPI_PORT, SPI_DEVICE)
    pga2320.max_speed_hz = 1000000  # PGA2320 max SPI Speed is 6.25MHz
except:
    print("Could not connect to SPI1 bus")

global events # Testing global to see if it will pass back to oden.py
selector = selectors.DefaultSelector()
try:
    IRsignal = InputDevice('/dev/input/by-path/platform-ir-receiver@12-event')
    Rotarysignal = InputDevice('/dev/input/by-path/platform-rotary@17-event')
    # This works because InputDevice has a `fileno()` method.
    selector.register(IRsignal, selectors.EVENT_READ)
    selector.register(Rotarysignal, selectors.EVENT_READ)
    events = Queue()
except (FileNotFoundError, PermissionError)as error:
    print("Something wrong with IR or Rotary Encoder", error)

# RAM Drive setup on /var/ram
# TODO: need to use RAM Drive until shutting down

# Write volume to file
def save_vol(vol):
    vol -= 40
    f = open('/home/volumio/bladelius/var/vol', 'w')
    f.write(str(vol))
    f.close()

# Get volume from file
def get_vol():
    f = open('/home/volumio/bladelius/var/vol', 'r')
    a = int(f.read())
    f.close()
    a += 40
    return a

# PCF8574 Pin States:
# BAL 1=                 D0=H,D1=X,D2=X,D3=X,D4=X,D5=L,D6=H,D7=H 0
# BAL 2=                 D0=H,D1=X,D2=X,D3=X,D4=X,D5=L,D6=H,D7=L 1
# LINE 1                 D0=X,D1=L,D2=L,D3=L,D4=H,D5=L,D6=L,D7=X 2
# LINE 2                 D0=X,D1=L,D2=L,D3=H,D4=L,D5=L,D6=L,D7=X 3 
# LINE 3                 D0=X,D1=L,D2=H,D3=L,D4=L,D5=L,D6=L,D7=X 4
# LINE 4                 D0=X,D1=H,D2=L,D3=L,D4=L,D5=L,D6=L,D7=X 5
# LINE 5 (TAPE)(LOOP)    D0=X,D1=L,D2=L,D3=L,D4=L,D5=H,D6=L,D7=X 6

def bal1(): #0xC1 / 0b1100 0001
    analogInput.write_byte(pcf_address, 0b11000001)
def bal2(): #0x41 / 0b0100 0001
    analogInput.write_byte(pcf_address, 0b01000001)
def line1(): #0x11 / 0b0001 0001
    analogInput.write_byte(pcf_address, 0b00010001)
def line2(): #0x09 / 0b0000 1001
    analogInput.write_byte(pcf_address, 0b00001001)
def line3(): #0x05 / 0b0000 0101
    analogInput.write_byte(pcf_address, 0b00000101)
def line4(): #0x03 / 0b0000 0011
    analogInput.write_byte(pcf_address, 0b00000011)
def line5(): #0x21 / 0b0010 0001
    analogInput.write_byte(pcf_address, 0b00100001)

switcherDigital = { 
    0: bal1,
    1: bal2,
    2: line1,
    3: line2,
    4: line3,
    5: line4,
    6: line5
}

def setAnalogInput(theInput):
    func = switcherDigital.get(theInput, "whoops")
    return func()

def listenRemote():
    try:
        while True:
            global curVol, curInput  # Needs to be global so values can be passed back to oden.py
            for key, mask in selector.select():
                device = key.fileobj
                for event in device.read():
                    if event.type == ecodes.EV_KEY:
                        events.put(event)
                        data = categorize(event)
                        remCode = data.keycode #event.value
                        if data.keystate >= 1: # Only on key down event, 2 is held down
                            if (remCode == btnVolUp) or (remCode == btnVolDwn):
                                if (curVol > volMax) and (remCode == btnVolUp):
                                    curVol = volMax
                                elif (remCode == btnVolUp):
                                    curVol += volStep
                                if (remCode == btnVolDwn) and (curVol < 0):
                                    curVol = 0
                                elif (remCode == btnVolDwn):
                                        curVol -= volStep
                                print("Current volume is: ", curVol)
                                dbVol = volTable[curVol]
                                pga2320.writebytes([dbVol, dbVol, dbVol, dbVol]) # 1 PGA2320/channel so 4 writes
                            if (remCode == btnSrcUp) or (remCode == btnSrcDwn):
                                if curInput == 6 and remCode == btnSrcUp:
                                    curInput = 0
                                else:
                                    if remCode == btnSrcUp:
                                        print("SOURCE + was pressed")
                                        curInput += 1
                                    else:
                                        print("SOURCE - was pressed")
                                        if curInput == 0:
                                            curInput = 6
                                        else:
                                            curInput -= 1
                                setAnalogInput(curInput)
                                text = analogInputs[curInput]
                                print("Current Input is: ", text)
                    if event.type == ecodes.EV_REL:
                        events.put(event)
                        curVol += event.value
                        if curVol < 0:
                            curVol = 0
                        elif curVol > volMax:
                            curVol = volMax
                        dbVol = volTable[curVol]
                        pga2320.writebytes([dbVol, dbVol, dbVol, dbVol]) # 1 PGA2320/channel so 4 writes
                        print("Rotary changed the volume to", curVol)
    except Exception as error:
        print("Had an IR exception", error)

def cleanup():
        pga2320.close()
        analogInput.close()
        IRsignal.close()
        print("I just finished cleaning up!")
        return
