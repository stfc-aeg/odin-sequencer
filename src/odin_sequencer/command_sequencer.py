"""CommandSequencer module

Module which facilitates communication to the command sequencer manager.

Viktor Bozhinov, STFC.
"""

import logging
import threading

from collections import deque
from datetime import datetime
from odin_sequencer import CommandSequenceManager, CommandSequenceError
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError


class CommandSequencer:
    """CommandSequencer object representing the command sequencer manager.

    Facilitates communcation to the command sequence manager.
    """

    def __init__(self, path_or_paths=None):
        """Initialise the CommandSequencer object.

        This constructor initialises the CommandSequencer object, creating a command
        sequencer manager, and building a parameter tree for it which allows clients
        to communicate with the manager.
        """

        self.initial_path_or_paths = path_or_paths

        self.detect_module_modifications = False
        self.reload = False
        self.module_reload_failed = False
        self.execute_seq_name = ''
        self.is_executing = False
        self.process_tasks = []
        self.process_group_tasks = {}
        self.log_messages = []
        self.last_message_timestamp = ''
        self.thread = None
        self.process_monitor_thread = None

        self.log_messages_deque = deque(maxlen=250)
        self.path_or_paths = []
        self.sequence_modules = {}

        self.manager = CommandSequenceManager()
        self.manager.register_external_logger(self.log)
        self.manager_initialised = False
        self._initialise_manager()

        self.param_tree = self._build_param_tree()

    def _initialise_manager(self, raise_on_error=False):
        """Initialises the command sequence manager and sets up paramters accordingly. This is
        called during initialisation of the CommandSequencer or subsequently on reload if the
        manager has not been correctly initialised before. This allows the CommandSequencer to
        instantiate a valid manager even if there are errors in the sequences.
        """

        try:
            self.manager.load(self.initial_path_or_paths)
            self.manager.resolve()
            # path_or_paths needed for when some modules fail to reload
            self.path_or_paths = list(self.manager.file_paths.values())
            self.sequence_modules = self.manager.sequence_modules
            self.manager_initialised = True
        except CommandSequenceError as e:
            err_msg = "Failed to load command sequence manager: {}".format(e)
            self.log(err_msg)
            logging.error(err_msg)
            if raise_on_error:
                raise CommandSequenceError(err_msg)


    def _build_param_tree(self):
        """Builds the parameter tree and as well as being called in the constructor, it is
        also called in set_reload so that the the parameter tree can get updated regardless
        of the outcome of the reloading process (i.e. adding information about any new sequences
        that were added in the loaded module or vice versa).
        """
        return ParameterTree({
            'sequence_modules': self.sequence_modules,
            'detect_module_modifications': (
                lambda: self.detect_module_modifications, self.set_detect_module_modifications),
            'module_modifications_detected': (self.module_modifications_detected, None),
            'reload': (lambda: self.reload, self.set_reload),
            'execute': (lambda: self.execute_seq_name, self.execute_sequence),
            'is_executing': (lambda: self.is_executing, None),
            'execution_progress': (lambda: self.manager.progress, None),
            'abort': (None, self.abort_sequence),
            'is_aborting': (lambda: self.manager.abort_sequence, None),
            'process_tasks': (lambda: self.process_tasks, None),
            'log_messages': (lambda: self.log_messages, None),
            'last_message_timestamp': (lambda: self.last_message_timestamp, self.get_log_messsages)
        })

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
        different routes depending on different states. If the manager has not yet been correctly
        initialised, that is attemped first. Otherwise, if module modifications process is enabled,
        it reloads the loaded modules that get modified during the process, otherwise it reloads
        all the loaded modules. An exception is raised if a problem occurs during the reloading
        process and sets module_reload_failed to True. The _build_param_tree is called regardless
        of the outcome of the reloading process. Exceptions are also raised if there are no
        modules loaded in the manager or a sequence is being executed.
        """

        if not self.manager_initialised:
            self._initialise_manager(True)
            self.param_tree = self._build_param_tree()
            return

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

        (seq_mod, seq) = next(
            ((mod_name, seq_module[seq_name])
                for (mod_name, seq_module) in sequence_modules.items() if
                    seq_name in seq_module
            ),
            None
        )

        kwargs = self._get_seq_param_values(seq)
        self.manager.reset_progress()
        self.is_executing = True
        self.execute_seq_name = seq_mod + "/" + seq_name
        self.thread = threading.Thread(target=self._execute, args=(seq_name,), kwargs=kwargs)
        self.thread.start()

    def _execute(self, seq_name, **kwargs):
        try:
            self.manager.execute(seq_name, **kwargs)
        except CommandSequenceError as error:
            self.manager.log_message('<b style="color:red">Execution error</b>: {}: {}'.format(seq_name, error))
            logging.error("Sequence execution error: {}: {}".format(seq_name, error))
        finally:
            self.is_executing = False
            self.execute_seq_name = ""
            if self.manager.abort_sequence:
                self.manager.log_message(
                    '<span style="color:orange">Execution of sequence "{}" aborted</span>'.format(seq_name)
                )
                logging.info("Execution of sequence {} aborted".format(seq_name))
                self.manager.abort_sequence = False

    def abort_sequence(self, abort):

        if abort and not self.is_executing:
            raise CommandSequenceError("Cannot abort when no sequence is executing")

        logging.debug("Aborting sequence with value {}".format(abort))
        self.manager.abort_sequence = abort

    def start_process_task(self, task_uuid):
        """Add task uuid to the process_tasks list"""
        self.process_tasks.append(task_uuid)

    def finish_process_task(self, task_uuid):
        """Remove task uuid from the process_tasks list"""
        try:
            self.process_tasks.remove(task_uuid)
        except ValueError as error:
            raise CommandSequenceError('Empty process task list while trying to remove {}'.format(task_uuid))

    def start_process_group_task(self, task_uuid, group_uuid):
        """
        Add task uuid to the process_group_tasks dictionary if it's the first group task
        add the group uuid to the process_tasks list
        """
        if group_uuid in self.process_group_tasks.keys():
            self.process_group_tasks[group_uuid].append(task_uuid)
            return False
        else:
            self.process_group_tasks[group_uuid] = [task_uuid]
            return True

    def finish_process_group_task(self, task_uuid, group_uuid):
        """
        Remove task uuid from the process_group_tasks dictionary if it's the last group task
        remove the group uuid from the process_tasks list
        """
        try:
            if len(self.process_group_tasks[group_uuid]) > 1:
                self.process_group_tasks[group_uuid].remove(task_uuid)
                return False
            else:
                self.process_group_tasks.pop(group_uuid)
                return True
        except ValueError as error:
            raise CommandSequenceError('Empty process task list while trying to remove group {} and task {}'.format(group_uuid, task_uuid))
    
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
                        raise CommandSequenceError("Invalid list: {} - {}".format(
                            param_name, error))

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
    
    def _add_context(self, name, obj):
        """This method adds an object to the manager context."""
        self.manager.add_context(name, obj)

    def _start_process_monitor(self, process_monitor):
        """Start thread in background for the process monitor."""
        self.process_monitor_thread = threading.Thread(target=process_monitor, args=(self.log, self.start_process_task, self.finish_process_task, self.start_process_group_task, self.finish_process_group_task), daemon=True)
        self.process_monitor_thread.start()    

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
