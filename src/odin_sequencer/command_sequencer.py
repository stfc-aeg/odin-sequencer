"""CommandSequencer module

Module which facilities communication to the command sequencer manager.
"""

from odin_sequencer import CommandSequenceManager, CommandSequenceError

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError


class CommandSequencer:
    """CommandSequencer object representing the command sequencer manager.

    Facilities communcation to the command sequence manager."""

    def __init__(self, path_or_paths=None):
        """Initialise the CommandSequencer object.

        This constructor initialises the CommandSequencer object, creating a command
        sequencer manager, and building a parameter tree for it which allows clients
        to communicate with the manager.
        """
        self.manager = CommandSequenceManager(path_or_paths)
        self.param_tree = ParameterTree({})

    def get(self, path):
        """Get parameters from the underlying parameter tree.

        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate CommandSequenceError.

        :param path: path of parameter tree to get
        :returns: parameter tree at that path as a dictionary
        """
        try:
            return self.param_tree.get(path)
        except ParameterTreeError as error:
            raise CommandSequenceError(error)

    def set(self, path, data):
        """Set parameter in the parameter tree.

        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate CommandSequenceError.

        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as error:
            raise CommandSequenceError(error)
