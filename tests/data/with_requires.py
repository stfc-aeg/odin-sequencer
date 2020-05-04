# Command sequences for testing CommandSequenceManager with a requires statement

requires = ['basic_sequences']
provides = ['layered_sequence']

def layered_sequence():

    val = basic_read()
    return val