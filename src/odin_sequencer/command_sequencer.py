from odin_sequencer import CommandSequenceManager, CommandSequenceError

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError


class CommandSequencer:

    def __init__(self, path_or_paths=None):

        self.manager = CommandSequenceManager(path_or_paths)
        self.auto_reload = False

        self.param_tree = ParameterTree({
            'sequences': {
                sequences_name: ({parameter.name: parameter.default for parameter in list(
                    self.manager.sequence_signatures[sequences_name].parameters.values())}) for sequences_name in self.manager.sequence_signatures
            },

            'auto_reload': (lambda: self.auto_reload, self.set_auto_reload)
        })

    def get(self, path):
        return self.param_tree.get(path)

    def set(self, path, data):
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise CommandSequenceError(e)

    def set_auto_reload(self, auto_reload):

        auto_reload = bool(auto_reload)

        if auto_reload != self.auto_reload:
            if auto_reload:
                self.manager.enable_auto_reload()
            else:
                self.manager.disable_auto_reload()

            self.auto_reload = auto_reload
