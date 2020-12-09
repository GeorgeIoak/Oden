#! /usr/bin/env python3
#coding: utf8

#import lirc
import time
import os
import sys
import spidev
import smbus
#import evdev
from evdev import InputDevice, categorize, ecodes
import config
import RPi.GPIO as GPIO

# Declare files to save status varialbe
file_mute = config.mute
file_vol = config.vol
file_input = config.input
file_power = config.power

btnVolUp =  'KEY_VOLUMEUP' #2075 #"vol-up"  # 0x1B
btnVolDwn = 'KEY_VOLUMEDOWN' #2076 #"vol-dwn"  # 0x1C
btnSrcUp =  'KEY_NEXT' #2071 #"next"  # 0x17
btnSrcDwn = 'KEY_PREVIOUS' #2072 #"prev"  # 0x18

digitalInputs = ["SPDIF 1", "SPDIF 2", "OPTICAL 1",
            "OPTICAL 2", "AES", "OPT 2", "DIG", "USB", " "]

analogInputs = ["BAL 1", "BAL 2", "LINE 1", "LINE 2",
            "LINE 3", "LINE 4", "LINE 5"]

curInput = 0  # What Source Input are we currently at
remCode = ''  # Current remote code with toggle bit masked off
curVol = curVolLeft = curVolRight = 0
old_vol = 0
volStep = 10

i2c_port_num = 1
pcf_address = 0x38  #temp address from 0x3B PCF8574A: A0=H, A1=H, A2=L
analogInput = smbus.SMBus(1)
analogInput.write_byte(pcf_address, 0x00) # Set PCF8574A to all outputs


# Open SPI bus instance for PGA2320
SPI_PORT = 1
SPI_DEVICE = 0
pga2320 = spidev.SpiDev()
pga2320.open(SPI_PORT, SPI_DEVICE)
pga2320.max_speed_hz = 1000000  # PGA2320 max SPI Speed is 6.25MHz
# pga2320.mode = 0b11 # was 3 in CircuitPython, can't change mode for SPI1

# sockid = lirc.init("odenremote") # Changed to using ir-keytable and events
try:
    IRsignal = InputDevice('/dev/input/event0')
except (FileNotFoundError, PermissionError):
    print("Something wrong with IR")


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

# BAL 1=                 D0=H,D1=X,D2=X,D3=X,D4=X,D5=L,D6=H,D7=H 0
# BAL 2=                 D0=H,D1=X,D2=X,D3=X,D4=X,D5=L,D6=H,D7=L 1
# LINE 1                 D0=X,D1=L,D2=L,D3=L,D4=H,D5=L,D6=L,D7=X 2
# LINE 2                 D0=X,D1=L,D2=L,D3=H,D4=L,D5=L,D6=L,D7=X 3 
# LINE 3                 D0=X,D1=L,D2=H,D3=L,D4=L,D5=L,D6=L,D7=X 4
# LINE 4                 D0=X,D1=H,D2=L,D3=L,D4=L,D5=L,D6=L,D7=X 5
# LINE 5 (TAPE)(LOOP)    D0=X,D1=L,D2=L,D3=L,D4=L,D5=H,D6=L,D7=X 6

def bal1(): #0xC1 / 0b1100 0001
    analogInput.write_byte(pcf_address, 0b11000001)

def bal2(): #0x41 0b0100 0001
    analogInput.write_byte(pcf_address, 0b01000001)

def line1(): #0x11 0b0001 0001
    analogInput.write_byte(pcf_address, 0b00010001)

def line2(): #0x09 0b0000 1001
    analogInput.write_byte(pcf_address, 0b00001001)

def line3(): #0x05 0b0000 0101
    analogInput.write_byte(pcf_address, 0b00000101)

def line4(): #0x03 0b0000 0011
    analogInput.write_byte(pcf_address, 0b00000011)

def line5(): #0x21 0b0010 0001
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


try:
    while True:
        #remCode = lirc.nextcode()
        #print(remCode)
        for event in IRsignal.read_loop():
            if event.type == ecodes.EV_KEY:
                data = categorize(event)
                print(event.value, hex(event.value), event.code, hex(event.code))
                remCode = data.keycode #event.value
                if data.keystate >= 1: # Only on key down event, 2 is held down
                    if (remCode == btnVolUp):
                        if (curVol >= 255):
                            curVol = curVol
                        else:
                            curVol += volStep
                    if (remCode == btnVolDwn):
                        if (curVol == 0):
                            curVol = curVol
                        else:
                            curVol -= volStep
                    print("Current volume is: ", curVol)
                    pga2320.writebytes([curVol, curVol, curVol, curVol])
                    # pga2320.close()
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
                    print("Current Input is: ", curInput)
                    text = analogInputs[curInput]
                    print(text)
finally:
    pga2320.close()
    analogInput.close()
    IRsignal.close()
    GPIO.cleanup()
