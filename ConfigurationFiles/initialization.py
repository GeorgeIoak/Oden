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

def init9068(dacAddress):
    theregs = { 6: 0b11110001,
                7: 0b11000000,
                8: 0b00000101,
               26: 0b00000001,
               24: 0b10000011,
               28: 0b10000100,  # bits 5:4 are format, 00 is I2S, 01 is LJ
               29: 0b01100000,  # Configure GPIO4 as an SPDIF Input
               31: 0b11000000,  # secret settings to get MQA working
               32: 0b10000000,
               33: 0b00000001,  # secret settings to get MQA working
               36: 0b00000000,
               37: 0b00000000,
               57: 0b00000001,
               57: 0b00000000,
               66: 0b00000100,  # set to syncronous mode so DSD512 works
               67: 0b11111111,
               77: 0b00000000,
              127: 0b00110000}
    theregs = {
                 4: 0b10000000,  # Set DAC CLK to ACLK1
                 6: 0b11110001,  # GPIO2: Set output high, GPIO1 lock status
                 7: 0b11000000,  # GPIO4: Set to PDM Data 2 Input
                 8: 0b00000101,  # GPIO5: is signal MQA
                26: 0b00010001,  # Low noise for AREF, Enable AREF
                24: 0b10000011,  # AREG_PDB analog reg enabled, DAC supply is 2.8V
                28: 0b10001100,  # Input Select Registers	Full Auto Select
                30: 0b00010000,  # DSD & DOP Operation + DAC Mix Select
                31: 0b11000000,  # Secret MQA Register
                32: 0b10000000,  # MQA Enable
                33: 0b00000001,  # Reserved	Changing fixed MQA Status
                41: 0b11101100,  # Volume Control Options
                41: 0b11101100,  # Volume Control Options
                42: 0b10101010,  # Automute Time
                43: 0b11111111,  # Automute Level
                44: 0b00000101,  # Automute Configuration
                52: 0b00000110,  # Filter Settings
                57: 0b00000000,  # THD+IIR
                60: 0b10100110,  # DAC THD Compensation C3
                61: 0b11111111,  # DAC THD Compensation C3
                67: 0b01011010,  # ASRC/DPLL Bandwidth not documented
                75: 0b00000111,  # NSMOD Configuration 1  [4:0] Reserved
                76: 0b00000000,  # NSMOD Configuration 2
    }
    with SMBus(bus=1, force=True) as bus:
        for reg,value in theregs.items():
            bus.write_byte_data(dacAddress, reg, value)

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
    init9068(dacAddress)

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

with open(setupFile, 'w') as theFile:
    settings.write(theFile)

# Now set the initial states of the outputs

def changeOutputs(powerUpDown):
    for i in theOutputs.keys():
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
