#!/usr/bin/env python

"""Tests for odin_sequencer package.

Some tests use the was_file_modified or _await_queue_size method to ensure that
a file was modified or that the file watcher, which runs in a separate thread,
detects and puts details of the modified files into the queue before the assertions
happen. Some tests also disable the auto reloading if it has been enabled to ensure
that the separate thread on which the file watcher runs is stopped.
"""

import time
import os
import importlib.util
import pytest

from odin_sequencer import CommandSequenceManager, CommandSequenceError
from .testutils import (modify_test_reload_module_file, modify_with_dependency_module_file,
                        get_last_modified_file_time, was_file_modified)


@pytest.fixture
def make_seq_manager(create_paths):
    """
    Factory test fixture that allows a sequence manager to be created with
    a particular file name or list of file names.
    """

    def _make_seq_manager(file_or_files=None):

        if not file_or_files:
            paths = None
        else:
            paths = create_paths(file_or_files)

        return CommandSequenceManager(paths)

    return _make_seq_manager


@pytest.fixture
def create_paths(shared_datadir):
    """
    Test fixture for creating file and directory paths that can be passed to
    the manager's load function to be loaded as modules.
    """

    def _create_paths(files_or_directories):

        if not isinstance(files_or_directories, list):
            return shared_datadir.joinpath(files_or_directories)

        return [shared_datadir.joinpath(
            file_or_directory) for file_or_directory in files_or_directories]

    return _create_paths


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


def _await_queue_size(manager, expected_queue_size):
    """
    This method Waits for the size of the queue to reach the given expected queue
    size number. The loop exists if the number is not reached after 15 seconds.
    param file_watcher: file watcher object from where the queue can be acccessed
    param expected_queue_size: the size that the queue needs to reach
    """
    for _ in range(30, 0, -1):
        if manager.file_watcher.modified_files_queue.qsize() == expected_queue_size:
            break
        time.sleep(0.5)


def test_empty_manager(make_seq_manager):
    """Test that a command sequence manager initialsed without any sequence files is empty."""
    manager = make_seq_manager()

    assert len(manager.modules) == 0
    assert len(manager.provides) == 0
    assert len(manager.requires) == 0
    assert len(manager.context) == 0
    assert len(manager.sequences) == 0


def test_basic_manager_loaded(make_seq_manager):
    """
    Test that a command sequence manager initialised with a single file exposes the
    correct sequence functions.
    """
    manager = make_seq_manager('basic_sequences.py')
    basic_return_value_seq_params = manager.sequences['basic_return_value']

    assert len(manager.modules) == 1
    assert len(manager.provides) == 1
    assert len(manager.requires) == 1
    assert len(manager.sequences) == 3
    assert len(basic_return_value_seq_params) == 1
    assert basic_return_value_seq_params['value']['default'] == 0
    assert basic_return_value_seq_params['value']['type'] == 'int'
    assert basic_return_value_seq_params['value']['value'] == 0
    assert hasattr(manager, 'basic_read')
    assert hasattr(manager, 'basic_write')


def test_load_with_illegal_syntax(make_seq_manager):
    """
    Test that loading a sequence module with illegal python syntax raises an error
    appropriately.
    """
    file_name = 'illegal_syntax.py'
    with pytest.raises(
            CommandSequenceError, match=r'Syntax error loading .*\/{}'.format(file_name)
    ):
        make_seq_manager(file_name)


def test_load_with_bad_import(make_seq_manager):
    """
    Test that loading a module with a bad import statement raises an error
    appropriately.
    """
    file_name = 'illegal_import.py'
    with pytest.raises(
            CommandSequenceError, match=r'Import error loading .*\/{}'.format(file_name)
    ):
        make_seq_manager(file_name)


def test_load_with_missing_module(make_seq_manager):
    """
    Test that loading a missing sequence module file into a manager raises an error
    appropriately.
    """
    file_name = 'does_not_exist.py'
    with pytest.raises(
            CommandSequenceError, match=r'Sequence module file .*\/{} not found'.format(file_name)
    ):
        make_seq_manager(file_name)


def test_load_with_directory_path(shared_datadir, make_seq_manager):
    """
    Test that all sequence module files in a specified directory are loaded into the manager.
    """
    directory = 'context_data'
    manager = make_seq_manager(directory)

    num_modules_in_dir = len(list(shared_datadir.joinpath(directory).glob('*.py')))
    assert len(manager.modules) == num_modules_in_dir
    assert len(manager.provides) == num_modules_in_dir
    assert len(manager.requires) == num_modules_in_dir


def test_load_with_module_and_directory_paths(shared_datadir, make_seq_manager):
    """
    Test that all specified module files and all module files inside a specified directory
    are loaded into the manager.
    """
    files = ['basic_sequences.py', 'with_requires.py']
    directory = 'context_data'
    manager = make_seq_manager(files + [directory])

    num_modules_in_dir = len(list(shared_datadir.joinpath(directory).glob('*.py')))
    assert len(manager.modules) == len(files) + num_modules_in_dir
    assert len(manager.provides) == len(files) + num_modules_in_dir
    assert len(manager.requires) == len(files) + num_modules_in_dir


def test_load_with_missing_directory(shared_datadir, make_seq_manager):
    """
    Test that retrieving module files from a missing directory raises an error appropriately.
    """
    directory_path = shared_datadir.joinpath('missing_directory')

    with pytest.raises(
            CommandSequenceError, match='Sequence directory {} not found'.format(directory_path)
    ):
        make_seq_manager(directory_path)


def test_explicit_module_load(make_seq_manager, create_paths):
    """
    Test that a module file is loaded into the manager when the load function
    is explicitly called.
    """
    manager = make_seq_manager()
    manager.load(str(create_paths('basic_sequences.py')))

    assert len(manager.modules) == 1


def test_explicit_module_load_when_auto_reloading_enabled(make_seq_manager, create_paths):
    """
    Test that newly loaded modules are added to the watch list when auto reloading is
    enabled.
    """
    files = ['basic_sequences.py', 'with_requires.py']
    file_paths = create_paths(files)
    manager = make_seq_manager(files[0])
    manager.enable_auto_reload()

    manager.load(str(file_paths[1]))

    assert manager.file_watcher is not None
    assert manager.auto_reload is True
    assert len(manager.file_watcher.watched_files) == len(files)
    assert str(file_paths[0]) in manager.file_watcher.watched_files
    assert str(file_paths[1]) in manager.file_watcher.watched_files

    manager.disable_auto_reload()


def test_reload_with_module_name(shared_datadir, make_seq_manager, create_tmp_module_files):
    """
    Test that a specific loaded module is successfully reloaded when its module name
    is provided to the reload function.
    """
    tmp_files = create_tmp_module_files
    module = tmp_files[0]
    manager = make_seq_manager(tmp_files)

    modify_test_reload_module_file(shared_datadir)
    manager.reload(module_names=module.stem)
    message = manager.generate_message()

    assert message == 'Message: Hello World'


def test_reload_with_file_path_object(shared_datadir, make_seq_manager, create_tmp_module_files):
    """
    Test that a specific loaded module is successfully reloaded when its path (in form
    of a Path object) is provided to the reload function.
    """
    tmp_files = create_tmp_module_files
    module = tmp_files[0]
    manager = make_seq_manager(tmp_files)

    modify_test_reload_module_file(shared_datadir)
    manager.reload(file_paths=module)
    message = manager.generate_message()

    assert message == 'Message: Hello World'


def test_reload_with_file_path_as_string(shared_datadir, make_seq_manager, create_tmp_module_files):
    """
    Test that a specific loaded module is successfully reloaded when its path (in form
    of a String) is provided to the reload function.
    """
    tmp_files = create_tmp_module_files
    module = tmp_files[0]
    manager = make_seq_manager(tmp_files)

    modify_test_reload_module_file(shared_datadir)
    manager.reload(file_paths=str(module))
    message = manager.generate_message()

    assert message == 'Message: Hello World'


def test_reload_multiple_modules(shared_datadir, make_seq_manager, create_tmp_module_files):
    """
    Test that specific loaded modules are successfully reloaded when their paths
    (in form of Path objects) are provided to the reload function.
    """
    tmp_files = create_tmp_module_files
    manager = make_seq_manager(tmp_files)

    modify_test_reload_module_file(shared_datadir)
    modify_with_dependency_module_file(shared_datadir)
    manager.reload(file_paths=tmp_files)
    message = manager.generate_message()

    assert message == 'Message: Hello World - Hello World'


def test_reload_without_module_names_and_file_paths(shared_datadir, make_seq_manager,
                                                    create_tmp_module_files):
    """
    Test that all the loaded modules are successfully reloaded when no module names or
    file paths are provided to the reload function.
    """
    tmp_files = create_tmp_module_files
    manager = make_seq_manager(tmp_files)

    modify_test_reload_module_file(shared_datadir)
    modify_with_dependency_module_file(shared_datadir)
    manager.reload()
    message = manager.generate_message()

    assert message == 'Message: Hello World - Hello World'


def test_reload_with_path_to_not_loaded_module(make_seq_manager, shared_datadir):
    """
    Test that passing a file path, that points to a module that has not been loaded,
    to the reload function raises the appropriate exception.
    """
    module = shared_datadir.joinpath('basic_sequences.py')
    manager = make_seq_manager()

    with pytest.raises(
            CommandSequenceError, match='Cannot reload file {} as it is not loaded '
                                        'into the manager'.format(module)
    ):
        manager.reload(file_paths=module)


def test_reload_with_not_loaded_module_name(make_seq_manager):
    """
    Test that passing a name of a module, that has not been loaded, to the reload
    function raises the appropriate exception.
    """
    module = 'basic_sequences'
    manager = make_seq_manager()

    with pytest.raises(
            CommandSequenceError, match='Cannot reload module {} as it is not loaded '
                                        'into the manager'.format(module)
    ):
        manager.reload(module_names=module)


def test_reload_when_byte_compiled_file_of_module_is_deleted(shared_datadir, make_seq_manager,
                                                             create_tmp_module_files):
    """
    Test that program does not break if the byte-compiled file of a specific module is
    deleted before the module is reloaded.
    """
    tmp_files = create_tmp_module_files
    module = tmp_files[0]
    manager = make_seq_manager(tmp_files)

    modify_test_reload_module_file(shared_datadir)

    os.remove(importlib.util.cache_from_source(module))
    manager.reload(file_paths=str(module))
    message = manager.generate_message()

    assert message == 'Message: Hello World'


def test_enable_auto_reload(make_seq_manager):
    """
    Test that _auto_reload is set to True and
    a file watcher is successfully created.
    """
    manager = make_seq_manager()

    manager.enable_auto_reload()

    assert manager.auto_reload is True
    assert manager.file_watcher is not None


def test_enable_auto_reload_when_auto_reloading_previously_enabled(shared_datadir,
                                                                   make_seq_manager):
    """
    Test that _auto_reload is set to True and the file watcher continues
    with watching files after being re-enabled.
    """
    files = ['basic_sequences.py', 'with_requires.py']
    basic_sequences_file_path = shared_datadir.joinpath(files[0])
    with_requires_file_path = shared_datadir.joinpath(files[1])
    manager = make_seq_manager(files)
    manager.enable_auto_reload()
    manager.disable_auto_reload()

    manager.enable_auto_reload()

    assert manager.file_watcher is not None
    assert manager.auto_reload is True
    assert manager.file_watcher.is_watching is True
    assert len(manager.file_watcher.watched_files) == len(files)
    assert str(basic_sequences_file_path) in manager.file_watcher.watched_files
    assert str(with_requires_file_path) in manager.file_watcher.watched_files

    manager.disable_auto_reload()


def test_disable_auto_reload(make_seq_manager):
    """
    Test that _auto_reload is set to False.
    """
    files = ['basic_sequences.py', 'with_requires.py']
    manager = make_seq_manager(files)
    manager.enable_auto_reload()

    manager.disable_auto_reload()

    assert manager.auto_reload is False


def test_manager_multiple_files(make_seq_manager):
    """
    Test that multiple module files can be
    loaded into the the sequence manager.
    """
    files = ['basic_sequences.py', 'no_provide.py']
    manager = make_seq_manager(files)

    assert len(manager.modules) == len(files)
    assert len(manager.provides) == len(files)
    assert len(manager.requires) == len(files)


def test_sequence_no_provide(make_seq_manager):
    """
    Test that a sequence file exports all functions for a sequence module without a
    'provides' statement.
    """
    manager = make_seq_manager('no_provide.py')

    assert len(manager.provides) == 1
    assert manager.provides['no_provide'] == ['default_read', 'default_write']


def test_sequence_mismatched_provide(make_seq_manager):
    """
    Test that loading a sequence file with a mismatched provide statement raises
    the appropriate exception.
    """
    file_stem = 'provide_mismatch'
    with pytest.raises(
            CommandSequenceError, match='{} does not implement missing_sequence listed '
                                        'in its provided sequences'.format(file_stem)
    ):
        make_seq_manager('{}.py'.format(file_stem))


def test_sequence_with_requires(make_seq_manager):
    """
    Test that loading a sequence file with a requires statement correctly resolves the
    required module.
    """
    manager = make_seq_manager(['basic_sequences.py', 'with_requires.py'])

    assert manager.requires['with_requires'] == ['basic_sequences']


def test_sequence_no_requires(make_seq_manager):
    """
    Test that loading a sequence file without a requires statement correctly resolves to any
    empty requires value in the manager
    """
    manager = make_seq_manager('basic_sequences.py')

    assert manager.requires['basic_sequences'] == []


def test_sequence_missing_requires(make_seq_manager):
    """
    Test that loading a sequence file with a requires statement but without the matching
    module raises an exception.
    """
    file = 'with_requires.py'
    with pytest.raises(
            CommandSequenceError, match='Failed to resolve required command sequence modules'
    ):
        make_seq_manager(file)


def test_file_load_explicit_resolve(make_seq_manager):
    """
    Test that loading a single sequence module into a manager with an explicit resolve argument
    yields a correct initalised manager.
    """
    manager = make_seq_manager('basic_sequences.py')

    assert len(manager.modules) == 1
    assert 'basic_sequences' in manager.modules


def test_execute_sequence(make_seq_manager):
    """
    Test that executing a sequence loaded from a file functions correctly, returning
    the appropriate value.
    """
    manager = make_seq_manager('basic_sequences.py')

    test_value = 90210
    ret_value = manager.execute('basic_return_value', test_value)

    assert ret_value == test_value


def test_execute_when_module_is_modified_while_auto_reload_enabled(shared_datadir, make_seq_manager,
                                                                   create_tmp_module_files):
    """
    Test that a module that has been modified while auto reloading
    was enabled is reloaded when it gets executed.
    """
    tmp_files = create_tmp_module_files
    manager = make_seq_manager(tmp_files)
    manager.enable_auto_reload()
    modify_test_reload_module_file(shared_datadir)
    _await_queue_size(manager, 1)

    message = manager.execute('generate_message')
    assert message == 'Message: Hello World'

    manager.disable_auto_reload()


def test_execute_when_modules_are_modified_while_auto_reload_enabled(shared_datadir,
                                                                     make_seq_manager,
                                                                     create_tmp_module_files):
    """
    Test that modules that have been modified while auto reloading
    was enabled are reloaded when they get executed.
    """
    tmp_files = create_tmp_module_files
    manager = make_seq_manager(tmp_files)
    manager.enable_auto_reload()
    modify_test_reload_module_file(shared_datadir)
    modify_with_dependency_module_file(shared_datadir)
    _await_queue_size(manager, 2)

    message = manager.execute('generate_message')
    assert message == 'Message: Hello World - Hello World'

    manager.disable_auto_reload()


def test_execute_when_module_is_modified_while_auto_reload_disabled(shared_datadir,
                                                                    make_seq_manager,
                                                                    create_tmp_module_files):
    """
    Test that a module that has been modified while auto reloading
    was disabled is not reloaded when it gets executed.
    """
    tmp_files = create_tmp_module_files
    test_reload_module = tmp_files[0]
    last_modified_time = get_last_modified_file_time(test_reload_module)
    manager = make_seq_manager(tmp_files)
    manager.enable_auto_reload()
    manager.disable_auto_reload()
    modify_test_reload_module_file(shared_datadir)
    file_modified = was_file_modified(test_reload_module, last_modified_time)

    if file_modified:
        message = manager.execute('generate_message')
        assert message == 'Message: World Hello'
    else:
        pytest.fail()


def test_attribute_func_when_module_is_modified_while_auto_reload_enabled(shared_datadir,
                                                                          make_seq_manager,
                                                                          create_tmp_module_files):
    """
    Test that a module that has been modified while auto reloading was enabled is reloaded
    when one of its functions is called through the manager attribute.
    """
    tmp_files = create_tmp_module_files
    manager = make_seq_manager(tmp_files)
    manager.enable_auto_reload()
    modify_test_reload_module_file(shared_datadir)
    _await_queue_size(manager, 1)

    message = manager.generate_message()

    assert message == 'Message: Hello World'

    manager.disable_auto_reload()


def test_attribute_func_when_module_sequence_is_added_auto_reload_enabled(shared_datadir,
                                                                          make_seq_manager,
                                                                          create_tmp_module_files):
    """
    Test that a module that has been modified to provide a new sequence while auto reloading is
    enabled is reloaded when the newly added sequence is called through the manager attribute.
    """
    tmp_files = create_tmp_module_files
    manager = make_seq_manager(tmp_files)
    manager.enable_auto_reload()
    modify_test_reload_module_file(shared_datadir)
    _await_queue_size(manager, 1)

    basic_seq_value = manager.basic_sequence(1)
    assert basic_seq_value == 1

    manager.disable_auto_reload()


def test_attribute_func_when_module_is_modified_while_auto_reload_disabled(shared_datadir,
                                                                           make_seq_manager,
                                                                           create_tmp_module_files):
    """
    Test that a module that has been modified while auto reloading was disabled is not reloaded
    when one of its functions is called through the manager attribute.
    """
    tmp_files = create_tmp_module_files
    test_reload_module = tmp_files[0]
    last_modified_time = get_last_modified_file_time(test_reload_module)
    manager = make_seq_manager(tmp_files)
    manager.enable_auto_reload()
    manager.disable_auto_reload()
    modify_test_reload_module_file(shared_datadir)
    file_modified = was_file_modified(test_reload_module, last_modified_time)

    if file_modified:
        message = manager.generate_message()
        assert message == 'Message: World Hello'
    else:
        pytest.fail()


def test_execute_missing_sequence(make_seq_manager):
    """
    Test that executing a missing sequence raises an exception correctly.
    the appropriate value.
    """
    manager = make_seq_manager('basic_sequences.py')
    missing_sequence = 'basic_missing'

    with pytest.raises(
            CommandSequenceError, match='Missing command sequence: {}'.format(missing_sequence)
    ):
        manager.execute(missing_sequence, 4567)


def test_add_context_to_manager(make_seq_manager, context_object):
    """
    Test that adding an object to the context of a manager makes that object available.
    """
    manager = make_seq_manager()
    obj_name = 'context_object'
    manager.add_context(obj_name, context_object)

    assert obj_name in manager.context
    assert id(context_object) == id(manager._get_context(obj_name))
    assert manager._get_context(obj_name).value == context_object.value


def test_access_context_in_sequence(make_seq_manager, context_object):
    """
    Test that accessing a context in a sequence works as as expected.
    """
    manager = make_seq_manager('context_data/context_sequences.py')
    context_access_seq_params = manager.sequences['context_access']
    obj_name = 'context_object'
    manager.add_context(obj_name, context_object)

    value = 3.141
    return_val = manager.context_access(value)

    assert return_val == value + 1
    assert len(manager.sequences) == 2
    assert len(manager.sequences['missing_context_obj']) == 0
    assert len(context_access_seq_params) == 1
    assert context_access_seq_params['value']['default'] == 0
    assert context_access_seq_params['value']['type'] == 'int'
    assert context_access_seq_params['value']['value'] == 0


def test_get_missing_context_object(make_seq_manager):
    """
    Test that attempting to access a missing context object raises an appropriate exception.
    """
    manager = make_seq_manager('context_data/context_sequences.py')
    obj_name = 'context_object'
    manager.add_context(obj_name, context_object)

    with pytest.raises(
            CommandSequenceError, match=r'Manager context does not contain \S+'
    ):
        manager.missing_context_obj()
