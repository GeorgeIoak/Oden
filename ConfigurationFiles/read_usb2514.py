#!/usr/bin/python
import smbus
bus = smbus.SMBus(1)

# read_i2c_block returns the byte count and then the values
# the returned array is limited to 32 bytes so you can only
# retrieve a maximum of 31 bytes so fetch 16 in each read

def readUSB2514():
	print("\033[32m0x{0:0{1}X}\033[0m").format(0,2),
	for w in range(0, 16, 1):
		print("\033[32m0x{0:0{1}X}\033[0m").format(w,2),
	print("")

	for x in range(0, 256, 16):
		list = bus.read_i2c_block_data(0x2c, x, 17) #Read in 16 bytes of data
		i = 0
		print("\033[32m0x{0:0{1}X}\033[0m").format(x,2), #Print data start address
		for value in list[1:]:
			newval = int(value) #convert string to integer
			print("0x{0:0{1}X}").format(newval,2), #print the formatted value
			i = i + 1
		print("")
	return

readUSB2514()

