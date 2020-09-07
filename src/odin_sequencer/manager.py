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
from .exceptions import CommandSequenceError
from .watcher import FileWatcherFactory

if sys.version_info < (3, 6, 0):  # pragma: no cover
    class ModuleNotFoundError(ImportError):
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
        self.context = {}
        self.file_paths = {}
        self._auto_reload = False
        self._file_watcher = None

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

        :param path_or_paths: names of file and directory paths to load. These can be of type String or Path.
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

            # If the module declares which sequence functions it provides, use that, otherwise assume
            # that all functions are to be made available
            if hasattr(module, 'provides'):
                provides = module.provides
            else:
                provides = [name for name, _ in inspect.getmembers(module, inspect.isfunction)]

            # Set the provided functions as attributes of this manager, so they are available
            # to be used by calling code. A reference to a partial function is set which calls
            # the execute function instead of the sequence function directly. This ensures
            # that modules get reloaded when auto reloading is enabled and the functions
            # are directly executed as callable functions from the manager itself. 
            for seq_name in provides:
                try:
                    seq_alias = seq_name + '_'
                    setattr(self, seq_alias, getattr(module, seq_name))
                    setattr(self, seq_name, partial(self.execute, seq_alias))
                except AttributeError:
                    raise CommandSequenceError(
                        "{} does not implement {} listed in its provided sequences".format(
                            module_name, seq_name)
                    )

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
            self.file_paths[module_name] = file_path

        # If requested, resolve dependencies for currently loaded modules
        if resolve:
            self.resolve()

        # Add the module(s) to the watch list if auto reloading is enabled
        if self._auto_reload and self._file_watcher:
            self._file_watcher.add_watch(path_or_paths)

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

            for i in range(len(file_paths)):
                file_path = file_paths[i]

                if not isinstance(file_path, Path):
                    file_path = Path(file_path)

                if file_path.stem not in self.modules:
                    raise CommandSequenceError(
                        'Cannot reload file {} as it is not loaded into the manager'.format(file_path)
                    )

                file_paths[i] = file_path

        if module_names:
            if not isinstance(module_names, list):
                module_names = [module_names]

            for module_name in module_names:
                if module_name not in self.modules: 
                    raise CommandSequenceError(
                        'Cannot reload module {} as it is not loaded into the manager'.format(module_name)
                    )

                if file_paths is None:
                    file_paths = []

                file_paths.append(self.file_paths[module_name])
            
        if module_names is None and file_paths is None:
            file_paths = list(self.file_paths.values())

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
            
            del(self.modules[name])
            del(self.file_paths[name])
            
    def enable_auto_reload(self):
        """ Enable auto reloading of modules currently loaded in the manager.

        This method enables auto reloading of all the modules that are currently loaded
        in the manager. A file watcher is created using the factory class and the paths 
        to all the loaded modules are passed to the file watcher so that it can watch 
        the modules for any modifications. Auto reloading is re-enabled and the already 
        created file watcher is reused if auto reloading is disabled when this function
        is called.
        """
        if not self._auto_reload:
            if not self._file_watcher:
                self._file_watcher = FileWatcherFactory.create_file_watcher(path_or_paths=list(self.file_paths.values()))
            else:
                self._re_enable_auto_reload()

            self._auto_reload = True

    def _re_enable_auto_reload(self):
        """Re-enables the auto reloading mechanism"""
        self._file_watcher.add_watch(list(self.file_paths.values()))
        self._file_watcher.run()

    def disable_auto_reload(self):
        """ Disable auto reloading of modules currently loaded in the manager.

        This method disabled auto reloading of all the modules that are currently loaded
        in the manager.
        """
        if self._file_watcher and self._auto_reload:
            self._file_watcher.stop()
            self._auto_reload = False

    def _retrieve_directory_files(self, directory_path):
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

        return [file for file in directory_path.glob('*.py')]

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
        if len(missing):
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
        if self._auto_reload and self._file_watcher:
            file_paths = []

            # Check the queue to see if it contains any modules that require reloading
            while not self._file_watcher.modified_files_queue.empty():
                file_path = self._file_watcher.modified_files_queue.get()
                file_paths.append(file_path)

            if file_paths:
                self._file_watcher.remove_watch(file_paths)
                self.reload(file_paths)

        if hasattr(self, sequence_name):

            return getattr(self, sequence_name)(*args, **kwargs)
        else:
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
