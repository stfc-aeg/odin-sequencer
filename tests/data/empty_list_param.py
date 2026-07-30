# Command sequence for testing SequenceManager with a sequence that has
# a list parameter whose default value contains no elements

provides = ['basic_seq']

def basic_seq(val=[]):

    return val