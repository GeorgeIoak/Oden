#! /usr/bin/env python3
#coding: utf8
# TODO Change this to a class (?) 

import os
import sys
sys.path.insert(0, r'/home/volumio/bladelius')
from ConfigurationFiles.config import*  # File locations for saving states
from ConfigurationFiles.initialization import changeOutputs as changeOutputs

import spidev
from smbus2 import SMBus
#import config
import threading
from evdev import InputDevice, categorize, ecodes
import selectors
from threading import Thread, Event
import asyncio
from queue import Queue
from time import*


import json
import ast
from configparser import ConfigParser, BasicInterpolation

btnVolUp =   'KEY_VOLUMEUP'   #2075 #"vol-up"   # 0x1B
btnVolDwn =  'KEY_VOLUMEDOWN' #2076 #"vol-dwn"  # 0x1C
btnSrcUp =   'KEY_NEXT'       #2071 #"next"     # 0x17
btnSrcDwn =  'KEY_PREVIOUS'   #2072 #"prev"     # 0x18
btnMenu =    'KEY_MODE'       #2073 #"display"  # 0x19
btnStandby = 'KEY_SLEEP'      #2068 #"standby"  # 0x14

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
prevInput = -1  # What Source Input was before
remCode = ''  # Current remote code with toggle bit masked off
curVol = 0
old_vol = dbVol = 0
volStep = 1
volMax = len(volTable) - 1  # PGA2320 range is 0-255 but we'll use a 0-100 lookup table

SPI_PORT = 1  # PGA2320 is at /dev/spidev1.0
SPI_DEVICE = 0
i2c_port_num = 1
isTyr = False
isOden = False
isDigital = False
isPhono = False
whatDoWeHave = []
theInputs = {}
theOutputs = {}
theBoards ={}
inMenu = False  # Used to reassign volume button for menu navigation

standbyFlag = 1  # Power up initialization turns things ON

# initialization.py needs to run first to modify setup.ini properly
setupFile = '/home/volumio/bladelius/ConfigurationFiles/setup.ini'
theProduct = ConfigParser(inline_comment_prefixes=(
    ';',), interpolation=BasicInterpolation())
theProduct.read(setupFile)  # File used to get product settings
theInputs.update(ast.literal_eval(theProduct['PRODUCT']['theinputs']))
theOutputs.update(ast.literal_eval(theProduct['PRODUCT']['theoutputs']))
theBoards.update(ast.literal_eval(theProduct['PRODUCT']['dacphonoboards']))
numInputs = len(theInputs) - 1  # Used for loops

dacAddress = int(theProduct['PRODUCT']['dacaddress'], 16)

volFile = '/home/volumio/bladelius/var/vol'     # File used to store state
volTemp = '/mnt/ramdisk/vol'                    # RAM disk storage
inputFile = '/home/volumio/bladelius/var/input'
inputTemp = '/mnt/ramdisk/input'
thedata = '' # Used for holding the file contents when read back

# Open SPI bus instance for PGA2320
try:
    pga2320 = spidev.SpiDev()
    pga2320.open(SPI_PORT, SPI_DEVICE)
    pga2320.max_speed_hz = 1000000  # PGA2320 max SPI Speed is 6.25MHz
    # 1 PGA2320/channel so 4 writes
    pga2320.writebytes([dbVol, dbVol, dbVol, dbVol])  # dbVol is 0 at power up so confirm mute state
    print(f"Muted PGA2320 by writing {dbVol} to the part")
except:
    print("Could not connect to SPI1 bus")

global events # Testing global to see if it will pass back to bladelius.py
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

# File handling for reading and saving system state
def file_service(filename, rw, filedata=''):
    with open(filename, rw) as f:
        if rw == 'r':
            thedata = int(f.read())
            return thedata
        else:
            f.write(str(filedata))

curInput = file_service(inputFile, 'r')
#curVol = file_service(volFile, 'r')  # Mike didn't want to change volume at powerup
print(f"Initialized curInput to {curInput} and volume to {curVol}")

def createBits(theInput, pcfAddress):
    bitsToSet   = list(theInputs.values())[theInput][1]
    bitsToClear = list(theInputs.values())[theInput][2]
    with SMBus(1) as i2cBus:
        currentBits = i2cBus.read_byte(pcfAddress)
    pcfBits = (currentBits | bitsToSet) & ~bitsToClear

def setInput(prevInput, theInput, dacAddress, firstStart=False):
    pcfAddress = list(theInputs.values())[theInput][0]
    bitsToSet = list(theInputs.values())[theInput][1]
    bitsToClear = list(theInputs.values())[theInput][2]
    with SMBus(1) as i2cBus:
        currentBits = i2cBus.read_byte(pcfAddress)
        pcfBits = (currentBits | bitsToSet) & ~bitsToClear
        i2cBus.write_byte(pcfAddress, pcfBits)
        pcfState = format(pcfBits, '#011_b')[2:11]
        print("PCF8574 with address of %s was sent this: %s" %
              (hex(pcfAddress), pcfState))
    last9068state = list(theInputs.values())[prevInput][3]
    cur9068state = list(theInputs.values())[theInput][3]
    lastInputBoard = list(theInputs.values())[prevInput][4]
    curInputBoard = list(theInputs.values())[theInput][4]
    print("Current Input is %d , Previous Input was %d"%(theInput, prevInput))
    print("Current Mode is %s , Previous Mode was %s"%(cur9068state, last9068state))
    if dacAddress:
        if (cur9068state != last9068state) or firstStart:  # 211120 Not needed since XMOS code change
            if cur9068state == 'I2S':
                inputSelect = 0b10000100  # Setting for Auto DSD/I2S
        #         syncMode =    0b00000100  # Enable Sync Mode for I2S
            else:
                inputSelect = 0b10000001  # Setting for SPDIF Input ONLY
        #         syncMode =    0b00000000  # Disable Sync Mode for SPDIF
            with SMBus(1) as i2cBus:
                i2cBus.write_byte_data(dacAddress, 28, inputSelect)  # Register 28 is Input Select
        #         i2cBus.write_byte_data(dacAddress, 66, syncMode)  # register 66 is Sync Settings
                #print("Write to %d address, Register 28, with %d" %(dacAddress, inputSelect))
    if (curInputBoard != lastInputBoard) or firstStart:
        pcfAddress = list(theBoards.values())[0][0]
        bitsToSet = list(theBoards.values())[0][1]
        bitsToClear = list(theBoards.values())[0][2]
        with SMBus(1) as i2cBus:
            currentBits = i2cBus.read_byte(pcfAddress)
        pcfBits = (currentBits | bitsToSet) & ~bitsToClear
        if curInputBoard != 'A':
            with SMBus(1) as i2cBus:
                i2cBus.write_byte(pcfAddress, pcfBits)
                pcfState = format(pcfBits, '#011_b')[2:11]
                print("PCF8574 with address of %s was sent this: %s" %
                    (hex(pcfAddress), pcfState))

def listenRemote():
#    try:
        while True:
            global curVol, prevInput, curInput, remCode  # Needs to be global so values can be passed back to bladelius.py
            for key, mask in selector.select():
                device = key.fileobj
                for event in device.read():
                    if event.type == ecodes.EV_KEY:
                        #events.put(event)
                        data = categorize(event)
                        if standbyFlag:  # Not in Standby so pass remote codes
                            remCode = data.keycode
                        elif (data.keycode != btnStandby):  # Clear all codes except for Standby
                            remCode = ""
                        else:
                            remCode = data.keycode
                        if data.keystate >= 1: # Only on key down event, 2 is held down
                            #print("inMenu is", inMenu)
                            events.put(event)
                            if ((remCode == btnVolUp) or (remCode == btnVolDwn)) and not inMenu:
                                if (curVol >= volMax) and (remCode == btnVolUp):
                                    curVol = volMax
                                elif (remCode == btnVolUp):
                                    curVol += volStep
                                if (remCode == btnVolDwn) and (curVol <= 0):
                                    curVol = 0
                                elif (remCode == btnVolDwn):
                                        curVol -= volStep
                                print("Current volume is: ", curVol)
                                dbVol = volTable[curVol]
                                pga2320.writebytes([dbVol, dbVol, dbVol, dbVol]) # 1 PGA2320/channel so 4 writes
                                file_service(volTemp, 'w', curVol)
                            if ((remCode == btnSrcUp) or (remCode == btnSrcDwn)) and not inMenu:
                                prevInput = curInput
                                if curInput == numInputs and remCode == btnSrcUp:
                                    curInput = 0
                                else:
                                    if remCode == btnSrcUp:
                                        print("SOURCE + was pressed", inMenu)
                                        curInput += 1
                                    else:
                                        print("SOURCE - was pressed")
                                        if curInput == 0:
                                            curInput = numInputs
                                        else:
                                            curInput -= 1
                                setInput(prevInput, curInput, dacAddress)
                                print("Current Input is: ", list(theInputs.keys())[curInput])
                                file_service(inputTemp, 'w', curInput)
                    if event.type == ecodes.EV_REL and standbyFlag:  # standbyFlag = 1 means system is ON
                        events.put(event)
                        curVol -= event.value  # Reversed logic because of wiring
                        if curVol < 0:
                            curVol = 0
                        elif curVol > volMax:
                            curVol = volMax
                        dbVol = volTable[curVol]
                        pga2320.writebytes([dbVol, dbVol, dbVol, dbVol]) # 1 PGA2320/channel so 4 writes
                        print("Rotary changed the volume to", curVol)
#    except Exception as error:
#        print("Had an IR exception", error)

def cleanup():
    pga2320.close()
#    i2cBus.close()
    IRsignal.close()
    print("I just finished cleaning up!")
    return
