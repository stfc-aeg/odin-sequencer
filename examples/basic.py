import odin_sequencer
from pathlib import Path

class TestDevice():

    def __init__(self, val):
        self.val = val

    def read_reg(self):
        print("In read reg")
        return self.val

    def write_reg(self, reg, vals):
        print("In write reg with reg {} vals {}".format(reg, vals))


def main():

    seq_dir = Path(__file__).resolve().parent.joinpath('sequences')

    seq_file_list  = [seq_dir.joinpath(seq_file) for seq_file in [
        './spi_commands.py', './example_sequences.py'
    ]]

    csm = odin_sequencer.CommandSequenceManager(seq_file_list)

    test_device = TestDevice(123)
    csm.add_context('test_device', test_device)

    csm.test_sequence()

if __name__ == '__main__':
    main()