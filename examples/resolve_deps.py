from odin_sequencer import CommandSequenceManager
from pathlib import Path
import time

def main():

    examples_dir = Path(__file__).resolve().parent

    paths = [examples_dir.joinpath(seq_file) for seq_file in [
        'dependencies/a.py', 'dependencies/b.py', 'dependencies/c.py', 'dependencies/d.py', 'dependencies/e.py'
    ]]
    
    csm = CommandSequenceManager(paths)

    print('sleeping')
    time.sleep(5) # Manually modify module code of a_three function while program is sleeping 

    csm.reload() # Reload all modules

    csm.a_one()
    csm.a_two()
    csm.a_three(5.678)
    csm.execute('a_three', 1.234, wibble='wobble')

if __name__ == '__main__':

    main()