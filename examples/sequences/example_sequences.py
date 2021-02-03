requires = ['spi_commands']
provides = ['test_sequence', 'another_sequence']

def test_sequence(a_val=123, b='hello'):

    print("Running test sequence")

    spi_read(8) #part of spi_commands.py
    spi_write([0x34]) # part of spi_commands.py
    #load_dacs()
    #calibrate()

    # Example loading a context
    dev = get_context('test_device')
    reg_val = dev.read_reg()
    print("Read register value", reg_val)

    queue = get_context('process_writer')
    queue.run('add', True, 4, 3)
    queue.group('add', True, range(10), 3)
    queue.group('dub', True, range(10))
    queue.run('dub', True, 5)

    for i in range(10):
        spi_write([i])
    
    reg_val += 1
    dev.write_reg(0x33, reg_val)

def another_sequence(c_val=False, d=1.234):

    pass
