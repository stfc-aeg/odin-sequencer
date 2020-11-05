# Sequences with list parameters for testing the command sequencer

provides = ['print_str_list', 'print_int_list', 'print_float_list', 'print_bool_list']

def print_str_list(val=['hello']):
    print(val)

def print_int_list(val=[0]):
    print(val)

def print_float_list(val=[1.5]):
    print(val)

def print_bool_list(val=[False]):
    print(val)