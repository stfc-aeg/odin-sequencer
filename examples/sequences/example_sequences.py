requires = ['spi_commands']
provides = ['test_sequence', 'another_sequence']

def test_sequence(a_val:int=123, b:str='hello'):

    print("Running test sequence")

    dev = get_context('test_device')

    spi_read(8)
    spi_write([0x34])
    #load_dacs()
    #calibrate()

    for i in range(10):
        spi_write([i])

    reg_val = dev.read_reg()
    print("Read register value", reg_val)

    reg_val += 1
    dev.write_reg(0x33, reg_val)

def another_sequence(c_val:bool=False, d=1.234):

    pass
