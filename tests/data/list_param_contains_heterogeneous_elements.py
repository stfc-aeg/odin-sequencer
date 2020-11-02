# Command sequence for testing CommandSequenceManager with a sequence that has
# a list parameter whose default value contains elements of different types

provides = ['basic_seq']

def basic_seq(val=[1, False]):

    return val