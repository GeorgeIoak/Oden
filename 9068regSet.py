#!/usr/local/bin/python39

import argparse
import ast

from smbus2 import SMBus
from configparser import ConfigParser, BasicInterpolation

configFile = '/home/volumio/bladelius/ConfigurationFiles/config.ini'

options = ConfigParser(inline_comment_prefixes=(
    ';',), interpolation=BasicInterpolation())
options.read(configFile)  # File used to store product configuration

dacAddress = int(options['DAC']['dacaddress'], 16)
theregs = ast.literal_eval(options['9068-INIT']['theregs'])

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
    for reg,value in theregs.items():
        bus.write_byte_data(dacAddress, reg, value)
        register = format(bus.read_byte_data(dacAddress, reg), '#011_b')[2:11]
        print("Register %s is: %s"%(reg, register))

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
    register = format(bus.read_byte_data(dacAddress, reg), '#011_b')[2:11]
    print("Register %s is: %s"%(reg, register))
    if value is not None:
        bus.write_byte_data(dacAddress, reg, value)
        register = format(bus.read_byte_data(dacAddress, reg), '#011_b')[2:11]
        print("Register %s is: %s"%(reg, register))


with SMBus(bus=1, force=True) as bus:
    if args.reg is not None:
        setReg(args.reg, args.value)
    elif args.i:
        init9068()
    else:
        for r in sorted(theregs.keys()):
            register = format(bus.read_byte_data(dacAddress, r), '#011_b')[2:11]
            print(f'Register {r:3} is: {register}')
