from odin_sequencer import CommandSequenceManager
from pathlib import Path
import sys
def main():

    examples_dir = Path(__file__).resolve().parent

    paths = [examples_dir.joinpath(seq_file) for seq_file in [
        'dependencies/a.py', 'dependencies/b.py', 'dependencies/c.py', 
        'dependencies/d.py', 'dependencies/e.py', 'dependencies/f.py'
    ]]

    csm = CommandSequenceManager(paths)

    csm.execute('f_one')

    csm.enable_auto_reload()

    input("Modify f_one function inside f.py or any of its dependency functions and then hit return")
    
    csm.f_one()

if __name__ == '__main__':

    main()