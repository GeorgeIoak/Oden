#! /usr/bin/env python3
#coding: utf8

import lirc
import time
import os
import sys
import spidev
import config
from pcf8574 import PCF8574
import RPi.GPIO as GPIO

# Declare files to save status varialbe
file_mute = config.mute
file_vol = config.vol
file_input = config.input
file_power = config.power

btnVolUp = "vol-up"  # 0x1B
btnVolDwn = "vol-dwn"  # 0x1C
btnSrcUp = "next"  # 0x17
btnSrcDwn = "prev"  # 0x18

selInput = ["SPDIF 1", "SPDIF 2", "OPTICAL 1",
            "OPTICAL 2", "AES", "OPT 2", "DIG", "USB", " "]

curInput = 0  # What Source Input are we currently at
remCode = 0  # Current remote code with toggle bit masked off
curVol = 0
old_vol = 0
volStep = 10
# Shouldn't need this but ...
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.OUT)  # SPI1 CS pin, RPi pin 13
GPIO.output(27, GPIO.HIGH)

i2c_port_num = 1
pcf_address = 0x39  # PCF8574A: A0=H, A1=L, A2=L
pcf = PCF8574(i2c_port_num, pcf_address)
pcf.port = [bool(curInput & (1 << i))
            for i in range(7, -1, -1)]  # Set all pins as outputs
# pcf.port = [bool(curInput & (1 << i)) for i in range(0, 8, 1)] # Set all pins as outputs

# Open SPI bus instance for PGA2320
SPI_PORT = 1
SPI_DEVICE = 0
pga2320 = spidev.SpiDev()
pga2320.open(SPI_PORT, SPI_DEVICE)
pga2320.max_speed_hz = 10000000  # PGA2320 max SPI Speed is 6.25MHz
# pga2320.mode = 0b11 # was 3 in CircuitPython, can't change mode for SPI1

sockid = lirc.init("odenremote")

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

# Set volume function


def set_volume(volume):
    gain = 31.5 - (0.5 * (255 - volume))
    dbgain = str(gain) + "dB"
    pga2320.open(1, 0)
    old_vol = get_vol()
    config.volume = volume
    save_vol(volume)
    if config.volume > old_vol:
        while old_vol < config.volume:
            old_vol += 1

# Set volume function


def set_volume(volume):
    gain = 31.5 - (0.5 * (255 - volume))
    dbgain = str(gain) + "dB"
    pga2320.open(1, 0)
    old_vol = get_vol()
    config.volume = volume
    save_vol(volume)
    if config.volume > old_vol:
        while old_vol < config.volume:
            old_vol += 1
            pga2320.writebytes([old_vol, old_vol])
            time.sleep(0.01)
    elif config.volume < old_vol:
        while old_vol > config.volume:
            old_vol -= 1
            pga2320.writebytes([old_vol, old_vol])
            time.sleep(0.01)
    elif config.volume == old_vol:
        pga2320.writebytes([old_vol, old_vol])
    pga2320.close()


try:
    while True:
        remCode = lirc.nextcode()
        print(remCode)
        if remCode != []:
            if (remCode[0] == btnVolUp):
                if (curVol >= 255):
                    curVol = curVol
                else:
                    curVol += volStep
            if (remCode[0] == btnVolDwn):
                if (curVol == 0):
                    curVol = curVol
                else:
                    curVol -= volStep
            print("Current volume is: ", curVol)
            GPIO.output(27, GPIO.LOW)
            pga2320.writebytes([curVol, curVol])
            pga2320.writebytes([curVol, curVol])  # just for safety measures
            GPIO.output(27, GPIO.HIGH)
            # pga2320.close()
            if (remCode[0] == btnSrcUp) or (remCode[0] == btnSrcDwn):
                if curInput == 8 and remCode[0] == btnSrcUp:
                    curInput = 0
                else:
                    if remCode[0] == btnSrcUp:
                        print("SOURCE + was pressed")
                        curInput += 1
                    else:
                        print("SOURCE - was pressed")
                        if curInput == 0:
                            curInput = 8
                        else:
                            curInput -= 1
                if curInput == 8:
                    #pcf.port = 0xF
                    pcf.port = [bool(curInput & (1 << i))
                                for i in range(7, -1, -1)]
                else:
                    #pcf.port = curInput
                    #pcf.port[curInput] = True
                    pcf.port = [bool(curInput & (1 << i))
                                for i in range(7, -1, -1)]
            print("Current Input is: ", curInput)
            print(pcf.port)
            text = selInput[curInput]
            print(text)
finally:
    pga2320.close()

