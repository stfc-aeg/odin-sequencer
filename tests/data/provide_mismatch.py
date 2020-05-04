# Command sequences for testing CommandSequenceManager with a mismatched provides statement

provides = ['default_read', 'default_write', 'missing_sequence']
def default_read():

    print("Default read")
    return 1234

def default_write():

    print("Default write")