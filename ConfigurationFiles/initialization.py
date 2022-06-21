#! /usr/bin/env python3
#coding: utf8

import os
import sys
import json
import ast
from configparser import ConfigParser, BasicInterpolation
from smbus2 import SMBus


i2c_port_num = 1
isTyr = False
isOden = False
isDigital = False
isPhono = False
whatDoWeHave = []
theInputs = {}
theOutputs = {}
selectBoards = {}

setupFile = '/home/volumio/bladelius/ConfigurationFiles/setup.ini'
configFile = '/home/volumio/bladelius/ConfigurationFiles/config.ini'

options = ConfigParser(inline_comment_prefixes=(';',), interpolation=BasicInterpolation())
options.read(configFile)  # File used to store product configuration

settings = ConfigParser(inline_comment_prefixes=(';',), interpolation=BasicInterpolation())
settings.read(setupFile)  # File used to get product settings

theregs = ast.literal_eval(options['9068-INIT']['theregs'])
menusettings = ast.literal_eval(
    settings['PRODUCT']['menusettings'])  # Last menu settings

# Routine to scan and return a list of I2C Devices on I2C1
def scan(force=False):
    devices = []
    for addr in range(0x03, 0x77 + 1):
        read = SMBus.read_byte, (addr,), {'force':force}
        write = SMBus.write_byte, (addr, 0), {'force':force}

        for func, args, kwargs in (read, write):
            try:
                with SMBus(1) as bus:
                    data = func(bus, *args, **kwargs)
                    devices.append(addr)
                    break
            except OSError as expt:
                if expt.errno == 16:
                    # just busy, maybe permanent by a kernel driver or just temporary by some user code
                    pass

    return devices

i2cDevices = scan(force=True)

def init9068(dacAddress, theregs):
    with SMBus(bus=1, force=True) as bus:
        for reg,value in theregs.items():
            bus.write_byte_data(dacAddress, reg, value)
        for reg, value in menusettings.items():  # Stored as a dict with list 
            bus.write_byte_data(dacAddress, value[0], value[1])

# TODO: Change to getting all devices from config.ini
tyr = ast.literal_eval(options['TYR']['pcfDevices'])
oden = ast.literal_eval(options['ODEN']['pcfDevices'])
digitalBoard = ast.literal_eval(options['DIGITAL']['pcfDevices'])
dacAddress = int(options['DAC']['dacaddress'], 16)

# Are we in an Oden or a Tyr/Ask
if set(tyr) <= set(i2cDevices):
    isTyr = True
    isOden = False
    whatDoWeHave.append("TYR")
elif set(oden) <= set(i2cDevices):
    isTyr = False
    isOden = True
    whatDoWeHave.append("ODEN")

# Check for the ES9068 DAC Chip
if (dacAddress in i2cDevices):
    whatDoWeHave.append("DAC")
    init9068(dacAddress, theregs)
else:
    dacAddress = 0x00

# Check for a Digital Board
if any(item in i2cDevices for item in digitalBoard):
    whatDoWeHave.append("DIGITAL")

for i in whatDoWeHave:
    #theInputs.update(json.loads(options[i]['inputarray']))
    theInputs.update(ast.literal_eval(options[i]['inputarray']))
    theOutputs.update(ast.literal_eval(options[i]['outputarray']))
    selectBoards.update(ast.literal_eval(options[i]['dacPhonoBoard']))
numInputs = len(theInputs) - 1  # Used for loops
numOutputs = len(theOutputs) - 1

settings.set('PRODUCT', 'whatdowehave', json.dumps(whatDoWeHave)) # Update what we found list
settings.set('PRODUCT', 'theInputs', json.dumps(theInputs)) # Update the inputs dictionary
settings.set('PRODUCT', 'theOutputs', json.dumps(theOutputs)) # Update the inputs dictionary
settings.set('PRODUCT', 'dacPhonoBoards', json.dumps(
    selectBoards))  # Update the settings to change input board
settings.set('PRODUCT', 'dacAddress', str(hex(dacAddress)))

with open(setupFile, 'w') as theFile:
    settings.write(theFile)

# Now set the initial states of the outputs

def changeOutputs(powerUpDown, skip=''):
    for i in theOutputs.keys():
        if i != skip:
            pcfAddress = theOutputs[i][0]
            with SMBus(1) as i2cBus:
                pcfBits = i2cBus.read_byte(pcfAddress)
            if ((theOutputs[i][2]) ^ powerUpDown) == 0:
                pcfBits &= ~(1<<theOutputs[i][1])
            elif ((theOutputs[i][2]) ^ powerUpDown) == 1:
                pcfBits |= (1 << theOutputs[i][1])
            with SMBus(1) as i2cBus:
                i2cBus.write_byte(pcfAddress, pcfBits)
                print("Changed to", format(pcfBits, '#011_b')[2:11])

changeOutputs(1) # 1 for PowerUp and 0 for PowerDown

'''
outputArray = { ; I2C Address, BitPosition, PowerUpState
  "Relay Control" : [%(U9)s,  7, 0],
  "Speaker Relay" : [%(U9)s,  6, 0],
  "Mute"          : [%(U9)s,  5, 1],
  "Bias Control"  : [%(U12)s, 0, 1]
  }
'''
