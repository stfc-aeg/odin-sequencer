import importlib.util
import inspect
from pathlib import Path

from .exceptions import CommandSequenceError

class CommandSequenceManager():

    def __init__(self, file_or_files=None):

        self.modules = {}
        self.requires = {}
        self.provides = {}
        self.context = {}

        if file_or_files:

            if not isinstance(file_or_files, list):
                file_or_files = [file_or_files] 

            for file in file_or_files:
                self.load_module(file, resolve=False)

            self.resolve()

    def load_module(self, file_path, resolve=True):

        module_name = Path(file_path).stem

        spec = importlib.util.spec_from_file_location(module_name, file_path) 
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, 'provides'):
            provides = module.provides
        else:
            provides = [name for name, _ in inspect.getmembers(module, inspect.isfunction)]

        for seq_name in provides:
            try:
                setattr(self, seq_name, getattr(module, seq_name))
            except AttributeError:
                raise CommandSequenceError(
                    "{} does not implement {} listed in its provided sequences".format(
                        module_name, seq_name)
                )

        if hasattr(module, 'requires'):
            requires = module.requires
        else:
            requires = []

        setattr(module, 'get_context', self._get_context)

        self.modules[module_name] = module
        self.provides[module_name] = provides
        self.requires[module_name] = requires

        if resolve:
            self.resolve()

    def resolve(self):

        dependencies = set()
        for reqs in self.requires.values():
            dependencies.update(reqs)

        missing = dependencies - set(self.modules.keys())

        if len(missing):
            raise CommandSequenceError(
                'Failed to resolve required command sequence modules (missing: {})'.format(
                    ','.join(missing)
                )
            )

        for name, module in self.modules.items():
            for required in self.requires[name]:
                for provided in self.provides[required]:
                    setattr(module, provided, getattr(self.modules[required], provided))

    def execute(self, sequence_name, *args, **kwargs):

        if hasattr(self, sequence_name):
            getattr(self, sequence_name)(*args, **kwargs)
        else:
            raise CommandSequenceError(
                'Missing command sequence: {}'.format(sequence_name)
            )

    def add_context(self, name, obj):

        self.context[name] = obj

    def _get_context(self, name):

        return self.context[name]




