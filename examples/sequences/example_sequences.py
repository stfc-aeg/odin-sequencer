requires = ['spi_commands', 'qem_plotcoarseMulti']
provides = ['test_sequence', 'another_sequence']

def test_sequence(a_val=123, b='hello'):

    print("Running test sequence")

    dev = get_context('test_device')
    spi_read(8) #part of spi_commands.py
    spi_write([0x34]) # part of spi_commands.py
    #load_dacs()
    #calibrate()

    queue = get_context('process_writer')
    queue.run('add', 4, 3)
    queue.group('add', range(10), 3)

    for i in range(10):
        spi_write([i])
    
    reg_val = dev.read_reg()
    print("Read register value", reg_val)

    reg_val += 1
    dev.write_reg(0x33, reg_val)

def another_sequence(c_val=False, d=1.234):

    pass
