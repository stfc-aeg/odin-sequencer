import os
from odin_sequencer import CommandSequenceManager

def main():

    seq_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dependencies')

    seq_file_list = [os.path.normpath(os.path.join(seq_dir, seq_file)) for seq_file in [
        './a.py', './b.py', './c.py', './d.py', './e.py'
    ]]
    
    csm = CommandSequenceManager(seq_file_list)

    csm.a_one()
    csm.a_two()
    csm.a_three(5.678)
    csm.execute('a_three', 1.234, wibble='wobble')

if __name__ == '__main__':

    main()