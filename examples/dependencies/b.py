requires = ['c', 'e']

provides = ['b_one', 'b_two']

def b_one():
    print("b_one")
    c_one()

def b_two():
    print("b_two")
    e_two()