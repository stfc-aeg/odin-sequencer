from odin_sequencer import CommandSequenceManager
from pathlib import Path
import time
import sys

def main():

    examples_dir = Path(__file__).resolve().parent

    paths = [examples_dir.joinpath(seq_file) for seq_file in [
        'dependencies/a.py', 'dependencies/b.py', 'dependencies/c.py', 'dependencies/d.py', 'dependencies/e.py'
    ]]

    csm = CommandSequenceManager(paths)

    csm.a_three(9.876)

    input("Modify a_three function inside a.py and then hit return")

    csm.reload(examples_dir.joinpath('dependencies/a.py'))

    csm.a_three(5.678)
    csm.execute('a_three', 1.234, wibble='wobble')

if __name__ == '__main__':

    main()