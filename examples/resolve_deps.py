from odin_sequencer import CommandSequenceManager
from pathlib import Path

def main():

    seq_dir = Path(__file__).resolve().parent.joinpath('dependencies')

    seq_file_list = [seq_dir.joinpath(seq_file) for seq_file in [
        './a.py', './b.py', './c.py', './d.py', './e.py'
    ]]
    
    csm = CommandSequenceManager(seq_file_list)

    csm.a_one()
    csm.a_two()
    csm.a_three(5.678)
    csm.execute('a_three', 1.234, wibble='wobble')

if __name__ == '__main__':

    main()