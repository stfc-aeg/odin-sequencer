# Basic command sequences for testing CommandSequenceManager

provides = ['basic_read', 'basic_write', 'basic_return_value']

def basic_read():

    print("Basic read")
    return 1234

def basic_write():

    print("Basic write")

def basic_return_value(value=0):

    return value