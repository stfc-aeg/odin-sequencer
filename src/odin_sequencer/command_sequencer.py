"""CommandSequencer module

Module which facilities communication to the command sequencer manager.

Viktor Bozhinov, STFC.
"""


from collections import deque
from datetime import datetime
from odin_sequencer import CommandSequenceManager, CommandSequenceError

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError


class CommandSequencer:
    """CommandSequencer object representing the command sequencer manager.

    Facilities communcation to the command sequence manager.
    """

    def __init__(self, path_or_paths=None):
        """Initialise the CommandSequencer object.

        This constructor initialises the CommandSequencer object, creating a command
        sequencer manager, and building a parameter tree for it which allows clients
        to communicate with the manager.
        """
        self.manager = CommandSequenceManager(path_or_paths)
        self.log_messages_deque = deque(maxlen=250)
        self.manager.register_external_logger(self.log)

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

    def log(self, *args, **kwargs):
        """This method is register as an external logger with the manager. Doing this results
        in all the print messages in the loaded sequences to be passed to this method. The method
        intercepts each print message, adds a timestamp to it and puts it onto the deque.
        """
        timestamp = datetime.now()
        message = ''

        for arg in args:
            message += str(arg)

        self.log_messages_deque.append((timestamp, message))

    def get_log_messsages(self, last_message_timestamp):
        """This method gets the log messages that are appended to the log message deque by the
        log function, and adds them to the log_messages variable. If a last message timestamp is
        provided, it will only get the subsequent log messages if there are any, otherwise it will
        get all of the messages from the deque.
        """
        logs = []
        if last_message_timestamp:
            last_message_timestamp = datetime.strptime(last_message_timestamp,
                                                       "%Y-%m-%d %H:%M:%S.%f")

            # Casting the deque to a list so that messages are not popped
            for index, (timestamp, log_message) in enumerate(list(self.log_messages_deque)):
                if timestamp > last_message_timestamp:
                    logs = list(self.log_messages_deque)[index:]
                    break
        else:
            logs = list(self.log_messages_deque)

        self.log_messages = [(str(timestamp), log_message) for timestamp, log_message in logs]
