import time
import pytest

from src.odin_sequencer.command_sequencer import CommandSequencer
from odin_sequencer import CommandSequenceManager, CommandSequenceError
from .testutils import (modify_test_reload_module_file, modify_test_reload_module_file_syntax_error,
                        modify_with_dependency_module_file, get_last_modified_file_time,
                        was_file_modified, await_queue_size)


@pytest.fixture
def create_command_sequencer(create_paths):

    def _create_command_sequencer(files_or_directories=None):
        if not files_or_directories:
            paths = None
        else:
            paths = create_paths(files_or_directories)

        return CommandSequencer(paths)

    return _create_command_sequencer

@pytest.fixture
def context_object():
    """
    Test fixture for creating a simple container object that can be loaded into
    the sequence manager context and accessed for test.
    """

    class ContextObject():
        """An example of a context object"""

        def __init__(self, value):
            self.value = value

        def increment(self, val):
            """Increments a given value by 1"""
            return val + 1

    return ContextObject(255374)

def _await_execution_complete(command_sequencer):
    for _ in range(15, 0, -1):
        time.sleep(1)
        if not command_sequencer.is_executing:
            break


def test_command_sequencer_with_no_paths(create_command_sequencer):
    command_sequencer = create_command_sequencer()

    assert type(command_sequencer.manager) == CommandSequenceManager
    assert len(command_sequencer.path_or_paths) == 0
    assert len(command_sequencer.param_tree.get('sequence_modules')['sequence_modules']) == 0


def test_command_sequencer_with_paths(create_command_sequencer, create_paths):
    file = 'basic_sequences.py'
    file_path = create_paths(file)

    command_sequencer = create_command_sequencer(file)

    seq_modules = command_sequencer.param_tree.get('sequence_modules')['sequence_modules']
    assert type(command_sequencer.path_or_paths) == list
    assert len(command_sequencer.path_or_paths) == 1
    assert file_path in command_sequencer.path_or_paths
    assert type(seq_modules) == dict
    assert len(seq_modules) == 1
    assert 'basic_sequences' in seq_modules


def test_get_param(create_command_sequencer):
    command_sequencer = create_command_sequencer('basic_sequences.py')

    detect_module_modifications = command_sequencer.get('detect_module_modifications')

    assert type(detect_module_modifications) == dict
    assert detect_module_modifications['detect_module_modifications'] is False


def test_get_missing_param(create_command_sequencer):
    missing_param = 'missing_param'
    command_sequencer = create_command_sequencer()

    with pytest.raises(
            CommandSequenceError, match='Invalid path: {}'.format(missing_param)
    ):
        command_sequencer.get(missing_param)


def test_set_param(create_command_sequencer):
    command_sequencer = create_command_sequencer('basic_sequences.py')

    command_sequencer.set('detect_module_modifications', True)
    detect_module_modifications = command_sequencer.get('detect_module_modifications')

    assert detect_module_modifications['detect_module_modifications'] is True

    command_sequencer.set('detect_module_modifications', False)


def test_set_missing_param(create_command_sequencer):
    missing_param = 'missing_param'
    command_sequencer = create_command_sequencer()

    with pytest.raises(
            CommandSequenceError, match='Invalid path: {}'.format(missing_param)
    ):
        command_sequencer.set(missing_param, 0)


def test_set_detect_module_modifications_to_true(create_command_sequencer):
    file = 'basic_sequences.py'
    command_sequencer = create_command_sequencer(file)

    command_sequencer.set_detect_module_modifications(True)
    detect_module_modifications = command_sequencer.get('detect_module_modifications')[
        'detect_module_modifications']

    assert detect_module_modifications is True
    assert command_sequencer.manager.module_watching is True

    command_sequencer.set_detect_module_modifications(False)


def test_set_detect_module_modifications_to_true_when_already_enabled(create_command_sequencer):
    file = 'basic_sequences.py'
    command_sequencer = create_command_sequencer(file)
    command_sequencer.set_detect_module_modifications(True)

    with pytest.raises(
            CommandSequenceError, match='A problem occurred while trying to start the ' +
                                        'Detect Modifications process: Module watching ' +
                                        'has already been enabled'
    ):
        command_sequencer.set_detect_module_modifications(True)

    command_sequencer.set_detect_module_modifications(False)


def test_set_detect_module_modifications_to_true_when_no_modules_loaded(create_command_sequencer):
    command_sequencer = create_command_sequencer()

    with pytest.raises(
            CommandSequenceError, match='A problem occurred while trying to start the ' +
                                        'Detect Modifications process: Cannot enable ' +
                                        'module watching when no modules are loaded'
    ):
        command_sequencer.set_detect_module_modifications(True)


def test_set_detect_module_modifications_to_false(create_command_sequencer):
    file = 'basic_sequences.py'
    command_sequencer = create_command_sequencer(file)
    command_sequencer.set_detect_module_modifications(True)

    command_sequencer.set_detect_module_modifications(False)
    detect_module_modifications = command_sequencer.get('detect_module_modifications')[
        'detect_module_modifications']

    assert detect_module_modifications is False
    assert command_sequencer.manager.module_watching is False


def test_set_detect_module_modifications_to_false_when_not_enabled(create_command_sequencer):
    command_sequencer = create_command_sequencer()

    with pytest.raises(
            CommandSequenceError, match='A problem occurred while trying to stop the ' +
                                        'Detect Modifications process: Module watching ' +
                                        'cannot be disabled as it has not been enabled'
    ):
        command_sequencer.set_detect_module_modifications(False)


def test_module_modifications_detected_when_no_modules_modified(shared_datadir,
                                                                create_command_sequencer,
                                                                create_tmp_module_files):
    tmp_files = create_tmp_module_files
    command_sequencer = create_command_sequencer(tmp_files)
    command_sequencer.set_detect_module_modifications(True)

    module_modifications_detected = command_sequencer.module_modifications_detected()

    assert module_modifications_detected is False

    command_sequencer.set_detect_module_modifications(False)


def test_module_modifications_detected_when_modules_modified(shared_datadir,
                                                             create_command_sequencer,
                                                             create_tmp_module_files):
    tmp_files = create_tmp_module_files
    command_sequencer = create_command_sequencer(tmp_files)
    command_sequencer.set_detect_module_modifications(True)
    modify_test_reload_module_file(shared_datadir)
    await_queue_size(command_sequencer.manager.module_watcher, 1)

    module_modifications_detected = command_sequencer.module_modifications_detected()

    assert module_modifications_detected is True

    command_sequencer.set_detect_module_modifications(False)


def test_module_modifications_detected_detect_when_module_modifications_disabled(
                                                            create_command_sequencer):
    command_sequencer = create_command_sequencer()

    module_modifications_detected = command_sequencer.module_modifications_detected()

    assert module_modifications_detected is False


def test_set_reload_to_true_when_detect_module_modifications_disabled(shared_datadir,
                                                                      create_command_sequencer,
                                                                      create_tmp_module_files):
    module_name = 'test_reload'
    new_seq_name = 'basic_sequence'
    tmp_files = create_tmp_module_files
    command_sequencer = create_command_sequencer(tmp_files)
    modify_test_reload_module_file(shared_datadir)

    command_sequencer.set_reload(True)

    seq_modules = command_sequencer.param_tree.get('sequence_modules')['sequence_modules']
    assert command_sequencer.module_reload_failed is False
    assert len(seq_modules[module_name]) == 2
    assert new_seq_name in seq_modules[module_name]


def test_set_reload_to_true_when_detect_module_modifications_enabled(shared_datadir,
                                                                     create_command_sequencer,
                                                                     create_tmp_module_files):
    module_name = 'test_reload'
    new_seq_name = 'basic_sequence'
    tmp_files = create_tmp_module_files
    command_sequencer = create_command_sequencer(tmp_files)

    test_reload_module = tmp_files[0]
    last_modified_time = get_last_modified_file_time(test_reload_module)
    modify_test_reload_module_file(shared_datadir)
    file_modified = was_file_modified(test_reload_module, last_modified_time)
    if file_modified:
        command_sequencer.set_detect_module_modifications(True)

        with_dependency_module = tmp_files[1]
        last_modified_time = get_last_modified_file_time(with_dependency_module)
        modify_with_dependency_module_file(shared_datadir)
        await_queue_size(command_sequencer.manager.module_watcher, 1)
        command_sequencer.set_reload(True)

        seq_modules = command_sequencer.param_tree.get('sequence_modules')['sequence_modules']
        assert command_sequencer.module_reload_failed is False
        assert len(seq_modules[module_name]) == 1
        assert new_seq_name not in seq_modules[module_name]

        command_sequencer.set_detect_module_modifications(False)
    else:
        pytest.fail(0)


def test_set_reload_to_true_when_module_failed_to_reload(shared_datadir, create_command_sequencer,
                                                         create_tmp_module_files):
    module_name = 'test_reload'
    tmp_files = create_tmp_module_files
    command_sequencer = create_command_sequencer(tmp_files)
    command_sequencer.set_detect_module_modifications(True)
    modify_test_reload_module_file_syntax_error(shared_datadir)
    await_queue_size(command_sequencer.manager.module_watcher, 1)
    try:
        command_sequencer.set_reload(True)
    except CommandSequenceError:
        pass

    new_seq_name = 'basic_sequence'
    test_reload_module = tmp_files[0]
    last_modified_time = get_last_modified_file_time(test_reload_module)
    modify_test_reload_module_file(shared_datadir)
    file_modified = was_file_modified(test_reload_module, last_modified_time)

    if file_modified:
        command_sequencer.set_reload(True)

        seq_modules = command_sequencer.param_tree.get('sequence_modules')['sequence_modules']
        assert command_sequencer.module_reload_failed is False
        assert len(seq_modules[module_name]) == 2
        assert new_seq_name in seq_modules[module_name]
    else:
        pytest.fail()

    command_sequencer.set_detect_module_modifications(False)


def test_set_reload_to_true_when_module_modified_with_syntax_error(shared_datadir,
                                                                   create_command_sequencer,
                                                                   create_tmp_module_files):
    tmp_files = create_tmp_module_files
    command_sequencer = create_command_sequencer(tmp_files)
    command_sequencer.set_detect_module_modifications(True)
    modify_test_reload_module_file_syntax_error(shared_datadir)
    await_queue_size(command_sequencer.manager.module_watcher, 1)
    test_reload_file_path = tmp_files[0]

    with pytest.raises(
            CommandSequenceError, match="A problem occurred during the reloading process: "
                                        "Syntax error loading {}".format(str(test_reload_file_path))
    ):
        command_sequencer.set_reload(True)
    assert command_sequencer.module_reload_failed is True

    command_sequencer.set_detect_module_modifications(False)


def test_set_reload_to_true_when_no_modules_loaded(create_command_sequencer):
    command_sequencer = create_command_sequencer()

    with pytest.raises(
            CommandSequenceError, match='Cannot start the reloading process as there are ' +
                                        'no sequence modules loaded'
    ):
        command_sequencer.set_reload(True)


def test_set_reload_to_true_while_sequence_is_executed(create_command_sequencer):
    file = 'basic_sequences.py'
    command_sequencer = create_command_sequencer(file)
    command_sequencer.is_executing = True

    with pytest.raises(
            CommandSequenceError, match='Cannot start the reloading process while a sequence ' +
                                        'is being executed'
    ):
        command_sequencer.set_reload(True)


def test_execute_sequence_string_list_param(create_command_sequencer):
    file = 'sequences_with_list_params.py'
    seq_name = 'print_str_list'
    param_name = 'val'
    path_to_seq = 'sequence_modules/sequences_with_list_params/' + seq_name
    new_list_val = ['Hello', 'World']
    data = {param_name: {'value': new_list_val}}
    command_sequencer = create_command_sequencer(file)
    command_sequencer.set(path_to_seq, data)

    command_sequencer.execute_sequence(seq_name)
    _await_execution_complete(command_sequencer)
    command_sequencer.get_log_messsages('')
    log_messages = command_sequencer.log_messages

    assert log_messages[0][1] == str(new_list_val)


def test_execute_sequence_int_list_param_int_values_passed_as_strings(create_command_sequencer):
    file = 'sequences_with_list_params.py'
    seq_name = 'print_int_list'
    param_name = 'val'
    path_to_seq = 'sequence_modules/sequences_with_list_params/' + seq_name
    new_list_val = ['0', '1']
    data = {param_name: {'value': new_list_val}}
    command_sequencer = create_command_sequencer(file)
    command_sequencer.set(path_to_seq, data)

    command_sequencer.execute_sequence(seq_name)
    _await_execution_complete(command_sequencer)
    command_sequencer.get_log_messsages('')
    log_messages = command_sequencer.log_messages

    assert log_messages[0][1] == '[0, 1]'


def test_execute_sequence_int_list_param_non_int_values_passed_as_strings(create_command_sequencer):
    file = 'sequences_with_list_params.py'
    seq_name = 'print_int_list'
    param_name = 'val'
    path_to_seq = 'sequence_modules/sequences_with_list_params/' + seq_name
    new_list_val = ['False', 'test']
    data = {param_name: {'value': new_list_val}}
    command_sequencer = create_command_sequencer(file)
    command_sequencer.set(path_to_seq, data)

    with pytest.raises(
            CommandSequenceError, match="Invalid list: {} - '{}' is not an int value".format(
                param_name, new_list_val[0])
    ):
        command_sequencer.execute_sequence(seq_name)

    command_sequencer.get_log_messsages('')
    log_messages = command_sequencer.log_messages
    assert command_sequencer.is_executing is False
    assert len(log_messages) == 0


def test_execute_sequence_float_list_param_float_values_passed_as_strings(create_command_sequencer):
    file = 'sequences_with_list_params.py'
    seq_name = 'print_float_list'
    param_name = 'val'
    path_to_seq = 'sequence_modules/sequences_with_list_params/' + seq_name
    new_list_val = ['0.5', '2.7']
    data = {param_name: {'value': new_list_val}}
    command_sequencer = create_command_sequencer(file)
    command_sequencer.set(path_to_seq, data)

    command_sequencer.execute_sequence(seq_name)
    _await_execution_complete(command_sequencer)
    command_sequencer.get_log_messsages('')
    log_messages = command_sequencer.log_messages

    assert log_messages[0][1] == '[0.5, 2.7]'


def test_execute_sequence_float_list_param_non_float_values_passed_as_strings(
                                                                        create_command_sequencer):
    file = 'sequences_with_list_params.py'
    seq_name = 'print_float_list'
    param_name = 'val'
    path_to_seq = 'sequence_modules/sequences_with_list_params/' + seq_name
    new_list_val = ['False', 'test']
    data = {param_name: {'value': new_list_val}}
    command_sequencer = create_command_sequencer(file)
    command_sequencer.set(path_to_seq, data)

    with pytest.raises(
            CommandSequenceError, match="Invalid list: {} - '{}' is not a float value".format(
                param_name, new_list_val[0])
    ):
        command_sequencer.execute_sequence(seq_name)

    command_sequencer.get_log_messsages('')
    log_messages = command_sequencer.log_messages
    assert command_sequencer.is_executing is False
    assert len(log_messages) == 0


def test_execute_sequence_float_list_param_bool_values_passed_as_strings(
                                                                    create_command_sequencer):
    file = 'sequences_with_list_params.py'
    seq_name = 'print_bool_list'
    param_name = 'val'
    path_to_seq = 'sequence_modules/sequences_with_list_params/' + seq_name
    new_list_val = ['True', 'False']
    data = {param_name: {'value': new_list_val}}
    command_sequencer = create_command_sequencer(file)
    command_sequencer.set(path_to_seq, data)

    command_sequencer.execute_sequence(seq_name)
    _await_execution_complete(command_sequencer)
    command_sequencer.get_log_messsages('')
    log_messages = command_sequencer.log_messages

    assert log_messages[0][1] == '[True, False]'


def test_execute_sequence_float_list_param_non_bool_values_passed_as_strings(
                                                                        create_command_sequencer):
    file = 'sequences_with_list_params.py'
    seq_name = 'print_bool_list'
    param_name = 'val'
    path_to_seq = 'sequence_modules/sequences_with_list_params/' + seq_name
    new_list_val = ['1', 'test']
    data = {param_name: {'value': new_list_val}}
    command_sequencer = create_command_sequencer(file)
    command_sequencer.set(path_to_seq, data)

    with pytest.raises(
            CommandSequenceError, match="Invalid list: {} - '{}' is not a bool value".format(
                param_name, new_list_val[0])
    ):
        command_sequencer.execute_sequence(seq_name)

    command_sequencer.get_log_messsages('')
    log_messages = command_sequencer.log_messages
    assert command_sequencer.is_executing is False
    assert len(log_messages) == 0


def test_execute_sequence_while_sequence_is_executed(create_command_sequencer):
    file = 'basic_sequences.py'
    command_sequencer = create_command_sequencer(file)
    command_sequencer.is_executing = True

    with pytest.raises(
            CommandSequenceError, match='Cannot execute command sequence while another one is ' +
                                        'being executed'
    ):
        command_sequencer.execute_sequence('basic_read')


def test_execute_sequence_while_reloading_process_in_progress(create_command_sequencer):
    file = 'basic_sequences.py'
    command_sequencer = create_command_sequencer(file)
    command_sequencer.reload = True

    with pytest.raises(
            CommandSequenceError, match='Cannot execute command sequence while the reloading ' +
                                        'process is in progress'
    ):
        command_sequencer.execute_sequence('basic_read')

    assert command_sequencer.is_executing is False


def test_execute_sequence_with_missing_sequence(create_command_sequencer):
    missing_sequence = 'basic_read'
    command_sequencer = create_command_sequencer()

    with pytest.raises(
            CommandSequenceError, match='Missing command sequence: {}'.format(missing_sequence)
    ):
        command_sequencer.execute_sequence(missing_sequence)

    assert command_sequencer.is_executing is False


def test_start_process_task(create_command_sequencer):
    uuid = 'uuid'
    command_sequencer = create_command_sequencer()
    
    command_sequencer.start_process_task(uuid)
    process_tasks = command_sequencer.process_tasks

    assert process_tasks == [uuid]


def test_finish_process_task(create_command_sequencer):
    uuid = 'uuid'
    command_sequencer = create_command_sequencer()
    command_sequencer.process_tasks = [uuid]
    
    command_sequencer.finish_process_task(uuid)
    process_tasks = command_sequencer.process_tasks

    assert process_tasks == []


def test_finish_process_task_with_empty_process_tasks_list(create_command_sequencer):
    uuid = 'uuid'
    command_sequencer = create_command_sequencer()

    with pytest.raises(
            CommandSequenceError, match='Empty process task list while trying to remove {}'.format(uuid)
    ):
        command_sequencer.finish_process_task(uuid)


def test_get_log_messages_with_no_last_message_timestamp(shared_datadir, create_command_sequencer,
                                                         create_tmp_module_files):

    tmp_files = create_tmp_module_files
    command_sequencer = create_command_sequencer(tmp_files)
    command_sequencer.execute_sequence('generate_message')
    _await_execution_complete(command_sequencer)

    command_sequencer.get_log_messsages('')
    log_messages = command_sequencer.log_messages

    assert len(log_messages) == len(list(command_sequencer.log_messages_deque))
    assert log_messages[0][1] == 'Executing generate_message'
    assert log_messages[1][1] == 'Executing get_message'


def test_get_log_messages_with_last_message_timestamp(create_command_sequencer,
                                                      create_tmp_module_files):

    tmp_files = create_tmp_module_files
    command_sequencer = create_command_sequencer(tmp_files)
    command_sequencer.execute_sequence('generate_message')
    _await_execution_complete(command_sequencer)
    last_message_timestamp = str(list(command_sequencer.log_messages_deque)[0][0])

    command_sequencer.get_log_messsages(last_message_timestamp)
    log_messages = command_sequencer.log_messages

    assert len(log_messages) == 1
    assert log_messages[0][1] == 'Executing get_message'


def test_add_context(create_command_sequencer, context_object):

    command_sequencer = create_command_sequencer()
    obj_name = 'context_object'
    command_sequencer._add_context(obj_name, context_object)

    assert obj_name in command_sequencer.manager.context
    assert id(context_object) == id(command_sequencer.manager._get_context(obj_name))
    assert context_object.value == command_sequencer.manager._get_context(obj_name).value
