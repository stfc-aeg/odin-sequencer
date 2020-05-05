"""Command sequence manager for ODIN control systems.

This module implements a command sequence manager for ODIN-based control systems. This allows
python scripts to be interactively loaded onto demand, resolve and dependencies betweem them
and make scripts functions available for use in a control system.

Tim Nicholls, UKRI STFC Detector Systems Software Group.
"""

import importlib.util
import inspect
from pathlib import Path
import sys

from .exceptions import CommandSequenceError

if sys.version_info < (3, 6, 0):  # pragma: no cover
    class ModuleNotFoundError(ImportError):
        """Derive ModuleNotFoundError exception for earlier python versions."""


class CommandSequenceManager():
    """
    Command sequencer manager class.

    The class implements a command sequencer manager, which allows one or more command
    sequence modules, i.e. script filess to be dynmically loaded and have their functions exposed
    to be executed as scripts.
    """

    def __init__(self, file_or_files=None):
        """Initialise the command sequence manager.

        This method initialises the manager, optionally loading one or more command sequence
        module files as specified and resolving them for use.

        :param file_or_files: (list) file names(s) to load
        """
        # Initialise empty data structures
        self.modules = {}
        self.requires = {}
        self.provides = {}
        self.context = {}

        # If one or more files have been specified, attempt to load and resolve them
        if file_or_files:

            if not isinstance(file_or_files, list):
                file_or_files = [file_or_files]

            for file in file_or_files:
                self.load_module(file, resolve=False)

            self.resolve()

    def load_module(self, file_path, resolve=True):
        """Load a sequence module file into the manager.

        This method attempts loads the specified module file into the manager, determine
        its required dependencie and what sequence functions it provides. If specified, the
        manager will then attempt to resolve all dependencies and make modules available.

        :param file_path: name of file path to load
        :param resolve: resolve loaded modules if True (default true)
        """
        # Get the module name from the stem of the file
        module_name = Path(file_path).stem

        # Create a module specification and attempt to load the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except SyntaxError as import_error:
            raise CommandSequenceError(
                'Syntax error loading {}: {}'.format(file_path, import_error)
            )
        except ModuleNotFoundError as import_error:
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
        # to be used by calling code
        for seq_name in provides:
            try:
                setattr(self, seq_name, getattr(module, seq_name))
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

        # If requested, resolve dependencies for currently loaded modules
        if resolve:
            self.resolve()

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
        can be executed directly as callable attributes of the manager itself.

        :param sequence_name: name of the loaded sequence function to execute
        :param *args: variable list of positional arguments to pass to function
        :param *kwargs: variable list of keyword arguments to pass to function
        :return: return value of called function
        """
        # Check if the named sequence function is loaded and execute it, otherwise raise an
        # exception
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
