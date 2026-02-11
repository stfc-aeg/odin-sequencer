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

    print("print (traditional formatting) args were time_a %s, time_b %s" % (time_a, time_b))
    log.debug("log (traditional formatting) args were time_a %s, time_b %s" % (time_a, time_b))

    print("print (string.format) args were time_a {}, time_b {}".format(time_a, time_b))
    log.info("log (string.format) args were time_a {}, time_b {}".format(time_a, time_b))

    print(f"print (f-string) args were time_a {time_a}, time_b {time_b}")
    log.warning(f"log (f-string) args were time_a {time_a}, time_b {time_b}")

    print("print (arg list) args were:", time_a, time_b)
    log.error("log (arg list) args were: %s %s", time_a, time_b)
    log.error("log (arg list, no formatting) args were:", time_a, time_b)
