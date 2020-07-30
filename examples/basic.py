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

    examples_dir = Path(__file__).resolve().parent

    paths = [examples_dir.joinpath(seq_file) for seq_file in [
        'sequences/spi_commands.py', 'sequences/example_sequences.py'
    ]]

    csm = odin_sequencer.CommandSequenceManager(paths)

    test_device = TestDevice(123)
    csm.add_context('test_device', test_device)

    csm.test_sequence()

if __name__ == '__main__':
    main()