#!/usr/local/bin/python39

import argparse

from smbus2 import SMBus

i2cAddr = 0x48
theregs = [4, 6, 7, 8, 24, 25, 26, 28, 29, 30, 31, 
           32, 33, 36, 37, 41, 57, 66, 67, 77, 122, 
           123, 124, 125, 126, 127]

def check_value(value):
    try:
        thevalue = int(value, 2)  # Check if it's binary
    except ValueError:
        try:
            thevalue = int(value)  # Check if it's an integer
        except ValueError:
            return "Not a valid number"
        return "Invalid binary number"
    finally:
        if not value.isdigit():
            raise argparse.ArgumentTypeError("Value should be a valid number!, %s is not" % value)

        if thevalue not in range(0, 256):
            raise argparse.ArgumentTypeError("%s is out of range, Valid values are 0 - 255" % thevalue)
        return thevalue

def check_reg(reg):
    if not reg.isdigit():
        raise argparse.ArgumentTypeError("Register Number must be an integer")
    ireg = int(reg)
    if ireg not in range(0, 254):
        raise argparse.ArgumentTypeError("%s is out of range, Valid Register Numbers are 0 - 254" % ireg)
    return ireg

def init9068():
    theregs = { 6: 0b11110001,
                7: 0b11000000,
                8: 0b00000101,
               26: 0b00000001,
               24: 0b10000011,
               28: 0b10001100, # bits 5:4 are format, 00 is I2S, 01 is LJ
               29: 0b01100000,  # Configure GPIO4 as an SPDIF Input
               31: 0b11000000,  # secret settings to get MQA working
               32: 0b10000000,
               33: 0b00000001,  # secret settings to get MQA working
               36: 0b00000000,
               37: 0b00000000,
               57: 0b00000001,
               57: 0b00000000,
               67: 0b11111111,
               77: 0b00000000,
              127: 0b00110000}
    for reg,value in theregs.items():
        bus.write_byte_data(i2cAddr, reg, value)
        register = format(bus.read_byte_data(i2cAddr, reg), '#011_b')[2:11]
        print("Register %s is: %s"%(reg, register))
    # Initialize PCF8574 U9 to set D4 bit
    try:
        bus.write_byte(0x20, 0x00) # Set PCF8574A to all outputs
    except OSError as e:
        print("Got", e, "error for address 0x20, is the board connected?")
        pass
    else:
        bus.write_byte(0x20, 0b00010000)
        pcf8574 = format(bus.read_byte(0x20), '#011_b')[2:11]
        print("PCF8574 U9 was set to: %s"%(pcf8574))


parser = argparse.ArgumentParser(description='Tool to Read and Set ES9068 Registers')

parser.add_argument('-r', '--reg',
                     choices=range(0, 254),
                     type=check_reg,
                     help='Register number, enter a decimal between 0-254',
                     metavar='Register #:[0-254]')
parser.add_argument('-v', '--value',
                     type=check_value,
                     required=False,
                     default=None,
                     help='value to write, 0b10101010')
parser.add_argument('-i',
                     action='store_true',
                     help='Configure Registers to enable output')

args = parser.parse_args()
#print(args)

def setReg(reg, value):
    register = format(bus.read_byte_data(i2cAddr, reg), '#011_b')[2:11]
    print("Register %s is: %s"%(reg, register))
    if value is not None:
        bus.write_byte_data(i2cAddr, reg, value)
        register = format(bus.read_byte_data(i2cAddr, reg), '#011_b')[2:11]
        print("Register %s is: %s"%(reg, register))


with SMBus(bus=1, force=True) as bus:
    if args.reg is not None:
        setReg(args.reg, args.value)
    elif args.i:
        init9068()
    else:
        for r in theregs:
            register = format(bus.read_byte_data(i2cAddr, r), '#011_b')[2:11]
            print(f'Register {r:3} is: {register}')
