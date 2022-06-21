from smbus2 import SMBus

data = 0x0 #Placeholder for read function
rw = 'r'

def pokeReg(reg, data=data, rw='r'):
    with SMBus(1) as bus:
        register = format(bus.read_byte_data(0x57, reg), '#011_b')[2:11]
        print("Register %s is: %s"%(reg, register))
        if (rw != 'r' ):
            bus.write_byte_data(0x57, reg, data)
            register = format(bus.read_byte_data(0x57, reg), '#011_b')[2:11]
            print("Register %s is: %s"%(reg, register))


