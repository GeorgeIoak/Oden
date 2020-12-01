#! /usr/bin/env python3
#coding: utf8

#import lirc
import time
import os
import sys
import spidev
import evdev
from evdev import InputDevice, categorize, ecodes
import config
from pcf8574 import PCF8574
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
curVol = 0
old_vol = 0
volStep = 10
# Shouldn't need this but ...
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.OUT)  # SPI1 CS pin, RPi pin 13
GPIO.output(27, GPIO.HIGH)

i2c_port_num = 1
pcf_address = 0x38  #temp address from 0x3B PCF8574A: A0=H, A1=H, A2=L
analogInput = PCF8574(i2c_port_num, pcf_address)
analogInput.port = [bool(curInput & (1 << i))
            for i in range(7, -1, -1)]  # Set all pins as outputs
# analogInput.port = [bool(curInput & (1 << i)) for i in range(0, 8, 1)] # Set all pins as outputs

# Open SPI bus instance for PGA2320
SPI_PORT = 1
SPI_DEVICE = 0
pga2320 = spidev.SpiDev()
pga2320.open(SPI_PORT, SPI_DEVICE)
pga2320.max_speed_hz = 10000000  # PGA2320 max SPI Speed is 6.25MHz
# pga2320.mode = 0b11 # was 3 in CircuitPython, can't change mode for SPI1

# sockid = lirc.init("odenremote") # Changed to using ir-keytable and events
device = InputDevice('/dev/input/event0')

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
    analogInput.port[0] = True
    analogInput.port[5] = False
    analogInput.port[6] = True
    analogInput.port[7] = True

def bal2(): #0x41 0b0100 0001
    analogInput.port[0] = True
    analogInput.port[5] = False
    analogInput.port[6] = True
    analogInput.port[7] = False

def line1(): #0x10 0b0001 0000
    analogInput.port[1] = False
    analogInput.port[2] = False
    analogInput.port[3] = False
    analogInput.port[4] = True
    analogInput.port[5] = False
    analogInput.port[6] = False

def line2():
    analogInput.port[1] = False
    analogInput.port[2] = False
    analogInput.port[3] = True
    analogInput.port[4] = False
    analogInput.port[5] = False
    analogInput.port[6] = False

def line3():
    analogInput.port[1] = False
    analogInput.port[2] = True
    analogInput.port[3] = False
    analogInput.port[4] = False
    analogInput.port[5] = False
    analogInput.port[6] = False

def line4():
    analogInput.port[1] = True
    analogInput.port[2] = False
    analogInput.port[3] = False
    analogInput.port[4] = False
    analogInput.port[5] = False
    analogInput.port[6] = False

def line5():
    analogInput.port[1] = False
    analogInput.port[2] = False
    analogInput.port[3] = False
    analogInput.port[4] = False
    analogInput.port[5] = True
    analogInput.port[6] = False

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
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                data = categorize(event)
                print(event.value, hex(event.value), event.code, hex(event.code))
                remCode = data.keycode #event.value
                if data.keystate == 1: # Only on key down event
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
                    GPIO.output(27, GPIO.LOW)
                    pga2320.writebytes([curVol, curVol])
                    pga2320.writebytes([curVol, curVol])  # just for safety measures
                    GPIO.output(27, GPIO.HIGH)
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
                    print(analogInput.port)
                    text = analogInputs[curInput]
                    print(text)
finally:
    pga2320.close()
    device.close()
    GPIO.cleanup()

