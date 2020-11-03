"""Command sequence manager for ODIN control systems.

This module implements a command sequence manager for ODIN-based control systems. This allows
python scripts to be interactively loaded onto demand, resolve and dependencies between them
and make scripts functions available for use in a control system.

Tim Nicholls, UKRI STFC Detector Systems Software Group.
"""

import importlib.util
import inspect
import sys
import os

from pathlib import Path
from functools import partial
from inspect import signature
from .exceptions import CommandSequenceError
from .watcher import FileWatcherFactory

if sys.version_info < (3, 6, 0):  # pragma: no cover
    class ModuleNotFoundError(ImportError):  # pylint: disable=redefined-builtin
        """Derive ModuleNotFoundError exception for earlier python versions."""


class CommandSequenceManager:
    """
    Command sequencer manager class.

    The class implements a command sequencer manager, which allows one or more command
    sequence modules, i.e. script files to be dynamically loaded and have their functions exposed
    to be executed as scripts.
    """

    def __init__(self, path_or_paths=None):
        """Initialise the command sequence manager.

        This method initialises the manager, optionally loading one or more command sequence
        module files as specified and resolving them for use.

        :param path_or_paths: path(s) to file module(s) to load
        """
        # Initialise empty data structures
        self.modules = {}
        self.requires = {}
        self.provides = {}
        self.sequence_modules = {}
        self.context = {}
        self.file_paths = {}
        self.module_watcher = None
        self.module_watching = False
        self.auto_reload = False

        # If one or more files have been specified, attempt to load and resolve them
        if path_or_paths:
            self.load(path_or_paths, False)
            self.resolve()

    def load(self, path_or_paths, resolve=True):
        """Load sequence module files into the manager.

        This method attempts to load the specified module file(s) into the manager, determine
        their required dependencies and what sequence functions they provide. If specified, the
        manager will then attempt to resolve all dependencies and make modules available. All
        module files in a directory are loaded if a path to a directory is specified.

        :param path_or_paths: names of file and directory paths to load. These can be of type
                                String or Path.
        :param resolve: resolve loaded modules if True (default true)
        """

        if not isinstance(path_or_paths, list):
            path_or_paths = [path_or_paths]

        file_paths = []

        for path in path_or_paths:

            if not isinstance(path, Path):
                path = Path(path)

            # Determines if path points to a directory
            if path.suffix != '.py':
                # Retrieve and add all module file paths from the specified directory to the list
                file_paths.extend(self._retrieve_directory_files(path))
                continue

            file_paths.append(path)

        for file_path in file_paths:

            # Get the module name from the stem of the file
            module_name = file_path.stem

            # Create a module specification and attempt to load the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except SyntaxError as import_error:
                raise CommandSequenceError(
                    'Syntax error loading {}: {}'.format(file_path, import_error)
                )
            except (ModuleNotFoundError, ImportError) as import_error:
                raise CommandSequenceError(
                    'Import error loading {}: {}'.format(file_path, import_error)
                )
            except FileNotFoundError:
                raise CommandSequenceError(
                    'Sequence module file {} not found'.format(file_path)
                )

            # If the module declares which sequence functions it provides, use that, otherwise
            # assume that all functions are to be made available
            if hasattr(module, 'provides'):
                provides = module.provides
            else:
                provides = [name for name, _ in inspect.getmembers(module, inspect.isfunction)]

            sequences = {}
            for seq_name in provides:
                # Do not load the sequence if one with the same name has already been registered
                if any(seq_name in val for val in self.provides.values()):
                    raise CommandSequenceError(
                        "Unable to load sequence '{}' from module '{}' as a sequence with the "
                        "same name has already being registered".format(seq_name, module_name)
                    )

                # Set the provided functions as attributes of this manager, so they are available
                # to be used by calling code. A reference to a partial function is set which calls
                # the execute function instead of the sequence function directly. This ensures
                # that modules get reloaded when auto reloading is enabled and the functions
                # are directly executed as callable functions from the manager itself.
                try:
                    seq_alias = seq_name + '_'
                    seq = getattr(module, seq_name)
                    setattr(self, seq_alias, seq)
                    setattr(self, seq_name, partial(self.execute, seq_alias))
                except AttributeError:
                    raise CommandSequenceError(
                        "{} does not implement {} listed in its provided sequences".format(
                            module_name, seq_name)
                    )

                # Extract information about the sequence parameters
                seq_params = seq_params = signature(seq).parameters.values()
                self._validate_sequence_parameters(seq_name, seq_params)
                sequences[seq_name] = self._build_sequence_parameter_info(seq_params)

            # If the module declares what dependencies it requires, use that, otherwise assume there
            # are none
            if hasattr(module, 'requires'):
                requires = module.requires
            else:
                requires = []

            # Set the manager context as an attribute of the module to allow access to external
            # functionality
            setattr(module, 'get_context', self._get_context)

            # Add the module information to the manager
            self.modules[module_name] = module
            self.provides[module_name] = provides
            self.requires[module_name] = requires
            self.sequence_modules[module_name] = sequences
            self.file_paths[module_name] = file_path

            # Add the module to the watch list if module watching is enabled
            if self.module_watching and self.module_watcher:
                self.module_watcher.add_watch(file_path)

        # If requested, resolve dependencies for currently loaded modules
        if resolve:
            self.resolve()

    def _validate_sequence_parameters(self, seq_name, seq_params):
        """ Validate the parameter(s) of a sequence.

        This method validates the parameters of a sequence, if it has any, by checking whether
        they have a default value. It does additional validation if the parameter is of type
        list. It raises an exception if no default value is provided for the parameter or if
        it is None.

        :param seq_name: the name of the sequence whose parameters are validated
        :param seq_params: list of sequence paramaters that need to be validated
        """
        for param in seq_params:
            if param.default is inspect.Parameter.empty or param.default is None:
                raise CommandSequenceError(
                    "'{}' parameter in '{}' sequence does not have a default value".format(
                        param.name, seq_name)
                )

            if type(param.default).__name__ == 'list':
                self._validate_list_parameter(seq_name, param)

    def _validate_list_parameter(self, seq_name, param):
        """ Validate a list parameter of a sequence.

        This method validates a list parameter of a sequence and ensures that it is not empty,
        does not contain a list element or elements of different types. It raises exceptions if
        any of these validations fail.

        :param param: the list parameter that needs to be validated
        :param seq_name: the name of the sequence to which the list parameter belongs to
        """
        if len(param.default) == 0:
            raise CommandSequenceError(
                "'{}' list parameter in '{}' sequence is empty".format(param.name, seq_name)
            )

        if any(isinstance(element, list) for element in param.default):
            raise CommandSequenceError(
                "'{}' list parameter in '{}' sequence contains a list element".format(
                    param.name, seq_name
                )
            )

        if not self._is_list_homogeneous(param.default):
            raise CommandSequenceError(
                "'{}' list parameter in '{}' sequence contains elements of different "
                "types".format(param.name, seq_name)
            )

    @staticmethod
    def _is_list_homogeneous(list_val):
        """ This method checks whether the elements in a list are of the same type.

        param list_val: the list that needs to be checked
        :return: True if the list are of the same type, otherwise False
        """
        return not any(not type(element) == type(list_val[0]) for element in list_val)

    def _build_sequence_parameter_info(self, params):
        """This method builds a dictionary that contains the parameter
        names that a sequence accepts, and their type and default value.

        :param params: the parameter(s) to extract and build information for
        :return: a dictionary with information about the parameters that the sequence accepts
        """
        return {
            param.name: {
                "value": param.default,
                "default": param.default,
                "type": self._get_parameter_type(param.default)
            } for param in params
        }

    @staticmethod
    def _get_parameter_type(param_default_val):
        param_type = type(param_default_val).__name__
        if param_type == 'list':
            param_type = 'list-{}'.format(type(param_default_val[0]).__name__)

        return param_type

    def reload(self, file_paths=None, module_names=None, resolve=True):
        """Reload currently loaded modules.

        This method attempts to reload all or specific sequence modules currently loaded
        into the manager. It does this by manually unloading all sequence modules and then
        loading them again and resolving their dependencies.

        :param module_names: module name(s) that require reloading (default: None)
        :param file_paths: path(s) to sequence module file(s) that require reloading (default: None)
        :param resolve: resolve loaded modules if True (default: true)
        """

        if file_paths:
            if not isinstance(file_paths, list):
                file_paths = [file_paths]

            for i, file_path in enumerate(file_paths):
                if not isinstance(file_path, Path):
                    file_path = Path(file_path)

                if file_path.stem not in self.modules:
                    raise CommandSequenceError(
                        'Cannot reload file {} as it is not loaded into the manager'.format(
                            file_path)
                    )

                file_paths[i] = file_path

        if module_names:
            if not isinstance(module_names, list):
                module_names = [module_names]

            for module_name in module_names:
                if module_name not in self.modules:
                    raise CommandSequenceError(
                        'Cannot reload module {} as it is not loaded into the manager'.format(
                            module_name)
                    )

                if file_paths is None:
                    file_paths = []

                file_paths.append(self.file_paths[module_name])

        if module_names is None and file_paths is None:
            file_paths = list(self.file_paths.values())

        if self.module_watching:
            self.module_watcher.remove_watch(file_paths)
        self._unload([file_path.stem for file_path in file_paths])

        self.load(file_paths, resolve)

    def _unload(self, module_names):
        """ This method unloads the specified modules by deleting them from the manager.

        :param: module_names: loaded modules that require unloading
        """

        for name in module_names:
            try:
                # The byte-compiled file associated to the module must be deleted
                # to ensure that the modified version of the module file is loaded
                os.remove(importlib.util.cache_from_source(self.file_paths[name]))
            except (FileNotFoundError, OSError):
                pass

            for provided in self.provides[name]:
                delattr(self, provided)

            del self.modules[name]
            del self.provides[name]
            del self.requires[name]
            del self.sequence_modules[name]
            del self.file_paths[name]

    def enable_module_watching(self):
        """ Enable watching for modifications in all modules that are currently loaded in the
        manager.

        This method enables watching for modifications in all the modules that are loaded in the
        manager. A module watcher is created using the factory class and the paths to all the
        loaded modules are passed to it so that it can watch the modules and detect any
        modifications. The watcher is re-enabled and the already created module watcher is reused
        if the watcher is disabled but was previously enabled. Exceptions are raised if enabling of
        module watching is attempted while enabled, or disabling while disabled.
        """
        if not self.modules:
            raise CommandSequenceError('Cannot enable module watching when no modules are loaded')

        if not self.module_watcher:
            self.module_watcher = FileWatcherFactory.create_file_watcher(
                path_or_paths=list(self.file_paths.values()))
        else:
            self.module_watcher.add_watch(list(self.file_paths.values()))
            try:
                self.module_watcher.run()
            except CommandSequenceError:
                raise CommandSequenceError('Module watching has already been enabled')

        self.module_watching = True

    def disable_module_watching(self):
        """ Disable the module watcher for all modules that are currently loaded in the manager.

        This method disables the watcher so that it will no longer watch for modifications in
        all the modules that are currently loaded in the manager. An exception is raised if
        disabling of the watcher is attempted while it is disabled or while it has not been
        instantiated at all.
        """
        try:
            self.module_watcher.stop()
            self.module_watching = False
        except (AttributeError, CommandSequenceError):
            raise CommandSequenceError(
                'Module watching cannot be disabled as it has not been enabled')

    def module_modifications_detected(self):
        """ Check if modifications of modules were detected or not.

        :return: True if modifications were detected, otherwise False
        """
        try:
            return not self.module_watcher.modified_files_queue.empty()
        except AttributeError:
            raise CommandSequenceError('Cannot check if modifications were detected because a ' +
                                       'module watcher has not been created')

    def get_modified_module_paths(self):
        """ Get a list of paths of the modules that were modified.

        :return: a list of paths to the modified modules
        """
        if not self.module_watcher:
            raise CommandSequenceError('Cannot get modified module paths because a module ' +
                                       'watcher has not been created')

        paths = []
        while not self.module_watcher.modified_files_queue.empty():
            path = self.module_watcher.modified_files_queue.get()
            paths.append(path)

        return paths

    def set_auto_reload(self, enabled=True):
        """ Disable/ enable auto reloading of modules currently loaded in the manager.

        This method disables/ enables auto reloading of all the modules that are
        currently loaded in the manager. The auto reloading is not done automatically,
        but rather on demand inside the execute function before a sequence is executed.

        :param enabled: Enables auto reload if True, or disables it otherwise (default True)
        """

        if enabled:
            if self.auto_reload:
                raise CommandSequenceError('Auto reloading has already been enabled')

            if not self.module_watching:
                try:
                    self.enable_module_watching()
                except CommandSequenceError as error:
                    raise CommandSequenceError(
                        'Cannot enable auto reloading due to: {}'.format(error))
        else:
            if not self.auto_reload:
                raise CommandSequenceError(
                    'Auto reloading cannot be disabled as it has not been enabled')

        self.auto_reload = enabled

    @staticmethod
    def _retrieve_directory_files(directory_path):
        """Retrieve paths to all sequence files in a directory.

        This method retrieves the paths to all the sequence files that are stored
        in a given directory. If the given directory does not exits, an exception
        is raised. Once retrieved, the paths are stored and returned as a list.

        :param directory_path: path to directory from which to retrieve paths to sequence files
        :return: a list of Path objects to all sequence files
        """

        if not directory_path.exists():
            # Raise an excpetion if the given directory does not exist
            raise CommandSequenceError(
                'Sequence directory {} not found'.format(directory_path)
            )

        return list(directory_path.glob('*.py'))

    def resolve(self):
        """Resolve dependencies for currently loaded modules.

        This method resolves required dependencies for currently loaded modules. If a
        required dependency is missing, an exception is raised. Once resolved, the sequence
        functions provided by required modules are exposed to other modules as necessary.
        """
        # Build the set of dependencies required across all loaded modules
        dependencies = set()
        for reqs in self.requires.values():
            dependencies.update(reqs)

        # Calculate if any dependencies are missing - if so, raise an exception.
        missing = dependencies - set(self.modules.keys())
        if missing:
            raise CommandSequenceError(
                'Failed to resolve required command sequence modules (missing: {})'.format(
                    ','.join(missing)
                )
            )

        # Iterate over loaded modules, injecting the functions provided by required dependencies
        # into each module to make available for use in sequence functions
        for name, module in self.modules.items():
            for required in self.requires[name]:
                for provided in self.provides[required]:
                    setattr(module, provided, getattr(self.modules[required], provided))

    def execute(self, sequence_name, *args, **kwargs):
        """Execute a command sequence.

        This method is a convenience for executing a loaded command sequence function, passing
        on positional and keyword arguments as appropriate. If the sequence function does not
        exist in the manager, an exception is raised. Note also that loaded sequence functions
        can be executed directly as callable attributes of the manager itself. Before calling
        the module, this method will also attempt to reload any modules that require reloading
        only if auto reloading is enabled.

        :param sequence_name: name of the loaded sequence function to execute
        :param *args: variable list of positional arguments to pass to function
        :param *kwargs: variable list of keyword arguments to pass to function
        :return: return value of called function
        """
        if self.auto_reload and self.module_modifications_detected:
            modified_module_paths = self.get_modified_module_paths()
            if modified_module_paths:
                self.reload(modified_module_paths)

        try:
            return getattr(self, sequence_name)(*args, **kwargs)
        except AttributeError:
            raise CommandSequenceError(
                'Missing command sequence: {}'.format(sequence_name)
            )

    def add_context(self, name, obj):
        """Add an object to the manager context.

        This method adds the specified object to the manager's context dictionary. This is
        intended to allow sequence functions controlled access to specific runtime features,
        objects or functions of the enclosing application without explicit importing of complex
        dependencies.

        :param name: name of the object to be added to the context
        :param obj: object to be added to the context
        """
        self.context[name] = obj

    def _get_context(self, name):
        """Get the named object from the manager context.

        This private method is bound into loaded sequence modules to allow access to named objects
        in the manager context from sequence modules.

        :param name: name of the object to access from the context
        :return: the named object
        """
        if name not in self.context:
            raise CommandSequenceError('Manager context does not contain {}'.format(name))

        return self.context[name]

    def __getattr__(self, name):
        """Solves the problem with AttributeError being raised when a newly added module sequence
        is programmatically called while auto-reload is enabled.

        If a new sequence is added to a module while the auto-reload is enabled, an attribute
        of that sequence will not be added to the manager until the reload logic is not executed
        in the execute function. As a result, programmatically calling the attribute for that
        sequence raises AttributeError. By deafult __getattr__ is called whenever a missing
        attribute is called, therefore the logic here attempts to reload modules that require
        reloading. AttributeError is raised if the sequence attribute does not exist after
        reloading is attempted.

        :param name: name of the missing attribute
        """
        if self.auto_reload and self.module_modifications_detected:
            modified_module_paths = self.get_modified_module_paths()
            if modified_module_paths:
                self.reload(modified_module_paths)

        if not any(name in val for val in self.provides.values()):
            raise AttributeError("Manager has no attribute '{}'".format(name))

        return getattr(self, name)
