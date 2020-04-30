requires = ['d', 'e']

provides = ['c_one', 'c_two']

def c_one():
    print("c_one")
    d_one()

def c_two():
    print("c_two")
    e_two()