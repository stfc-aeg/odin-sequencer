"""CommandSequencer module

Module which facilities communication to the command sequencer manager.

Viktor Bozhinov, STFC.
"""


import threading

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

    def set_detect_module_modifications(self, detect_module_modifications):
        """Enable/ disable detect module modifications.

        This method enables or disables the detect module modifications process based on the bool
        value that is passed to it. Exceptions are raised if True is passed while the detect module
        modifications process is enabled, or False is passed while the detect module modifications
        process is disabled.

        :param detect_module_modifications
        """
        if detect_module_modifications:
            try:
                self.manager.enable_module_watching()
            except CommandSequenceError as error:
                raise CommandSequenceError('A problem occurred while trying to start the ' +
                                           'Detect Modifications process: {}'.format(error))
        else:
            try:
                self.manager.disable_module_watching()
            except CommandSequenceError as error:
                raise CommandSequenceError('A problem occurred while trying to stop the ' +
                                           'Detect Modifications process: {}'.format(error))

        self.detect_module_modifications = detect_module_modifications

    def module_modifications_detected(self):
        """Check whether module modifications were detected.

        This method checks if module modifications were detected only if the the detect module
        modifications process is enabled.

        :return: False if the detect module modifications process is not enabled or not module
                modifications were detected, otherwise True
        """
        if self.detect_module_modifications is False:
            return False

        return self.manager.module_modifications_detected()

    def set_reload(self, reload):
        """This method attempts to start the reloading process if True is passed to it. It takes
        different routes depending on different states. If module modifications process is enabled,
        it reloads the loaded modules that get modified during the process, otherwise it reloads
        all the loaded modules. An exception is raised if a problem occurs during the reloading
        process and sets module_reload_failed to True. The _build_param_tree is called regardless
        of the outcome of the reloading process. Exceptions are also raised if there are no
        modules loaded in the manager or a sequence is being executed.
        """
        sequence_modules = self.param_tree.get('sequence_modules')['sequence_modules']
        if not sequence_modules:
            raise CommandSequenceError(
                'Cannot start the reloading process as there are no sequence modules loaded')

        if self.is_executing:
            raise CommandSequenceError(
                'Cannot start the reloading process while a sequence is being executed')

        if reload:
            try:
                if self.module_reload_failed:
                    self._load_failed_modules()
                else:
                    self._reload()
                # Resolving at the end to avoid dependency issues
                self.manager.resolve()
                self.module_reload_failed = False
            except CommandSequenceError as error:
                self.module_reload_failed = True
                raise CommandSequenceError(
                    'A problem occurred during the reloading process: {}'.format(error))
            finally:
                self.param_tree = self._build_param_tree()

    def _reload(self):
        """This method reloads the loaded modules that get modified during the detect module
        modifications process (if enabled), otherwise it reloads all the loaded modules.
        """
        modified_module_paths = None

        if self.detect_module_modifications and self.module_modifications_detected():
            modified_module_paths = self.manager.get_modified_module_paths()

        # All modules are reloaded when manager's reload receives None for the file_paths arg
        self.manager.reload(file_paths=modified_module_paths, resolve=False)

    def _load_failed_modules(self):
        """This method attempts to load the modules that failed to previously reload

        If module_reload_failed is True, next time the set_reload method is called, this method
        will take all the module paths from path_or_paths (contains all module paths that were
        initially loaded into the manager), compares them against the manager's path_or_paths
        (contains all module paths that are currently loaded) and attempt to load the ones that
        are missing. It also attempts to reload any loaded modules that were modified.
        """
        for path in self.path_or_paths:
            if path not in self.manager.file_paths.values():
                self.manager.load(path_or_paths=path, resolve=False)

        # Reload any modules that were modified during the above load process
        if self.module_modifications_detected():
            self._reload()

    def execute_sequence(self, seq_name):
        """Attempt to execute the passed sequence.

        This method attempts to execute passed sequence name. Before doing that, it will check if
        the sequence is loaded and will raise an exception if it is not. If it is, it will get
        the parameter values that were set for that sequence from the parameter tree (only if the
        sequence has parameters). The execution happens on a separate thread so that the main thread
        does not get blocked if the sequence takes a long time to execute.Exceptions are raised if
        the method is called while the reloading process is in progress or a sequence is being
        executed.
        """
        if self.is_executing:
            raise CommandSequenceError(
                'Cannot execute command sequence while another one is being executed')

        if self.reload:
            raise CommandSequenceError(
                'Cannot execute command sequence while the reloading process is in progress')

        sequence_modules = self.param_tree.get('sequence_modules')['sequence_modules']
        if not any(seq_name in seq_module for seq_module in sequence_modules.values()):
            raise CommandSequenceError('Missing command sequence: {}'.format(seq_name))

        seq = next((seq_module[seq_name] for seq_module in sequence_modules.values() if
                    seq_name in seq_module), None)

        kwargs = self._get_seq_param_values(seq)
        self.is_executing = True
        self.thread = threading.Thread(target=self._execute, args=(seq_name,), kwargs=kwargs)
        self.thread.start()

    def _execute(self, seq_name, **kwargs):
        self.manager.execute(seq_name, **kwargs)
        self.is_executing = False

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

    def _get_seq_param_values(self, seq):
        """This method gets parameter values for the provided sequence from the parameter tree.
        The values get casted if the parameter is a list. An exception is raised if a problem
        occurs during the casting process.

        :return: dictionary containing the sequence parameters and the values that were set
        """
        kwargs = {}
        for param_name in seq:
            param_val = seq[param_name]['value']
            param_type = seq[param_name]['type']

            if param_type.startswith('list'):
                list_type = param_type.split('-')[1]

                if list_type != 'str':
                    try:
                        param_val = self._cast_list(list_type, param_val)
                    except ValueError as error:
                        raise CommandSequenceError("Invalid list: {}".format(error))

            kwargs.update({
                param_name: param_val
            })

        return kwargs

    def _cast_list(self, list_type, list_val):
        """This method decides the type of list casting that is required."""
        if list_type == 'bool':
            list_val = map(self._val_to_bool, list_val)
        elif list_type == 'int':
            list_val = map(self._val_to_int, list_val)
        elif list_type == 'float':
            list_val = map(self._val_to_float, list_val)

        return list(list_val)

    @staticmethod
    def _val_to_bool(val):
        if type(val != str):
            val = str(val)

        if val.lower().strip() == 'true':
            return True
        elif val.lower().strip() == 'false':
            return False
        else:
            raise ValueError("'{}' is not a bool value".format(val))

    @staticmethod
    def _val_to_int(val):
        if type(val != str):
            val = str(val)

        try:
            return int(val.strip())
        except ValueError:
            raise ValueError("'{}' is not an int value".format(val))

    @staticmethod
    def _val_to_float(val):
        if type(val != str):
            val = str(val)

        try:
            return float(val.strip())
        except ValueError:
            raise ValueError("'{}' is not a float value".format(val))
