requires = ['spi_commands']
provides = ['test_sequence', 'another_sequence', 'no_params', 'test','abortable_sequence_test', 'logging_sequence']

import time

def test_sequence(a_val=123, b='hello'):

    print("Running test sequence")
    print("a_val ", a_val)
    spi_read(8) #part of spi_commands.py
    spi_write([0x34]) # part of spi_commands.py
    #load_dacs()
    #calibrate()

    # Example loading a context
    dev = get_context('test_device')
    reg_val = dev.read_reg()
    print("Read register value", reg_val)

    # queue = get_context('process_writer')
    # queue.run('add', True, 4, 3)
    # queue.group('add', True, range(10), 3)
    # queue.group('dub', True, range(10))
    # queue.run('dub', True, 5)

    for i in range(10):
        spi_write([i])
    
    reg_val += 1
    dev.write_reg(0x33, reg_val)

    sub_func("hello")

def sub_func(argument='no'):
    print("Running sub_func with argument {}".format(argument))

def another_sequence(c_val=False, d=1.234):

    pass

def abortable_sequence_test(num_loops=100, loop_delay=0.1):

    set_progress(0, num_loops)

    for i in range(num_loops):
        if i % 10 == 0:
            print("Loop count {}".format(i))

        time.sleep(loop_delay)
        set_progress(i+1, num_loops)
        if abort_sequence():
            print("Aborting sequence")
            break

    print("Sequence complete")

def no_params():

    set_progress(0, 10)

    for i in range(10):
        time.sleep(2.0)
        print("no_params no.{}".format(i))
        set_progress(1+1, 10)


def test(num_numbers=10):

    for x in range(10):
        time.sleep(2.0)
        print(x)

def logging_sequence(time_a=1, time_b=2):
    """Simple sequence to demonstrate logging functionality."""
    # % string formatting
    log.debug("Sequence has begun with timer_a set to %d", time_a)
    log.debug("and timer_b set to %d" % time_b)
    # string .format()
    log.info("Starting first timer of {:d} seconds".format(time_a))
    time.sleep(time_a)
    # f formatting
    log.info(f"First timer complete, starting second timer of {time_b} seconds")
    time.sleep(time_b)
    log.warning("Sequence is almost complete, ending in one second")
    time.sleep(1)
    log.error(f"Pretend that something went wrong here.")
    print("Print statements default to info level in the sequencer only. Level is otherwise None")
    print(f"Sequence complete")