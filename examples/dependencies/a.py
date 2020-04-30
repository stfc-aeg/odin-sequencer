requires = ['b', 'd']

provides = ['a_one', 'a_two', 'a_three']

def a_one():
    print("a_one")
    b_one()

def a_two():
    print("a_two")
    d_two()

def a_three(arg, wibble="hmm"):
    print("a_three: arg={} wibble={}".format(arg, wibble))