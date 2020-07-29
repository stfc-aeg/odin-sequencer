#!/usr/bin/env python

"""Tests for odin_sequencer package."""

import pytest

from pathlib import Path
from odin_sequencer import CommandSequenceManager, CommandSequenceError

@pytest.fixture
def create_paths(shared_datadir):
    """
    Test fixture for creating file and directory paths that can be passed to 
    the manager's load function to be loaded as modules.
    """
    def _create_paths(files_or_directories):

        return [shared_datadir.joinpath(file_or_directory) for file_or_directory in files_or_directories]
    
    return _create_paths
    

@pytest.fixture
def context_object():
    """
    Test fixture for creating a simple container object that can be loaded into
    the sequence manager context and accessed for test.
    """
    class ContextObject(object):

        def __init__(self, value):
            self.value = value

        def increment(self, val):
            return val + 1

    return ContextObject(255374)

def test_empty_manager(create_paths):
    """Test that a command sequence manager initialsed without any sequence files is empty."""
    manager = CommandSequenceManager()

    assert len(manager.modules) == 0
    assert len(manager.provides) == 0
    assert len(manager.requires) == 0
    assert len(manager.context) == 0

def test_basic_manager_loaded(create_paths):
    """
    Test that a command sequence manager initialised with a single file exposes the
    correct sequence functions.
    """
    manager = CommandSequenceManager()
    paths = create_paths(['basic_sequences.py'])
    manager.load_module(paths)

    assert len(manager.modules) == 1
    assert len(manager.provides) == 1
    assert len(manager.requires) == 1
    assert hasattr(manager, 'basic_read')
    assert hasattr(manager, 'basic_write')

def test_load_module_with_illegal_syntax(create_paths):
    """
    Test that loading a sequence module with illegal python syntax raises an error
    appropriately.
    """
    file_name = 'illegal_syntax.py'
    with pytest.raises(
        CommandSequenceError, match=r'Syntax error loading .*\/{}'.format(file_name)
    ):
        manager = CommandSequenceManager()
        paths = create_paths([file_name])
        manager.load_module(paths)

def test_load_module_with_bad_import(create_paths):
    """
    Test that loading a module with a bad import statement raises an error
    appropriately.
    """
    file_name = 'illegal_import.py'
    with pytest.raises(
        CommandSequenceError, match=r'Import error loading .*\/{}'.format(file_name)
    ):
        manager = CommandSequenceManager()
        paths = create_paths([file_name])
        manager.load_module(paths)

def test_load_missing_module(create_paths):
    """
    Test that loading a missing sequence module file into a manager raises an error
    appropriately.
    """
    file_name = 'does_not_exist.py'
    with pytest.raises(
        CommandSequenceError, match=r'Sequence module file .*\/{} not found'.format(file_name)
    ):
        manager = CommandSequenceManager()
        paths = create_paths([file_name])
        manager.load_module(paths)

def test_load_module_with_directory_path(shared_datadir, create_paths):
    """
    Test that all sequence module files in a specified directory are loaded into the manager.
    """
    directory = 'context_data'
    manager = CommandSequenceManager()
    paths = create_paths([directory])
    manager.load_module(paths, False)
    manager.resolve()

    num_modules_in_dir = len(list(shared_datadir.joinpath(directory).glob('*.py')))
    assert len(manager.modules) == num_modules_in_dir
    assert len(manager.provides) == num_modules_in_dir
    assert len(manager.requires) == num_modules_in_dir

def test_load_module_with_file_and_directory_paths(shared_datadir, create_paths):
    """
    Test that all specified module files and all module files inside a specified directory
    are loaded into the manager.
    """
    files = ['basic_sequences.py', 'with_requires.py']
    directory = 'context_data'
    manager = CommandSequenceManager()
    paths = create_paths(files + [directory])
    manager.load_module(paths, False)
    manager.resolve()

    num_modules_in_dir = len(list(shared_datadir.joinpath(directory).glob('*.py')))
    assert len(manager.modules) == len(files) + num_modules_in_dir
    assert len(manager.provides) == len(files) + num_modules_in_dir
    assert len(manager.requires) == len(files) + num_modules_in_dir

def test_retrieve_directory_files_with_existing_directory(shared_datadir, create_paths):
    """
    Test that paths to all sequence files that are stored inside an existing directory
    are retrieved.
    """
    
    directory_path = shared_datadir.joinpath('context_data')
    manager = CommandSequenceManager()
    file_paths = manager.retrieve_directory_files(directory_path)

    num_modules_in_dir = len(list(directory_path.glob('*.py')))
    assert len(file_paths) == num_modules_in_dir

def test_retrieve_directory_files_missing_directory(shared_datadir, create_paths):

    directory_path = shared_datadir.joinpath('missing_directory')

    with pytest.raises(CommandSequenceError,
        match='Sequence directory {} not found'.format(directory_path)
    ):
        manager = CommandSequenceManager()
        manager.retrieve_directory_files(directory_path)

def test_manager_multiple_files(create_paths):
    """
    Test that multiple module files can be loaded into the the sequence manager.
    """

    files = ['basic_sequences.py', 'no_provide.py']
    manager = CommandSequenceManager()
    paths = create_paths(files)
    manager.load_module(paths, False)
    manager.resolve()

    assert len(manager.modules) == len(files)
    assert len(manager.provides) == len(files)
    assert len(manager.requires) == len(files)

def test_sequence_no_provide(create_paths):
    """
    Test that a sequence file exports all functions for a sequence module without a 
    'provides' statement.
    """
    manager = CommandSequenceManager()
    paths = create_paths(['no_provide.py'])
    manager.load_module(paths)

    assert len(manager.provides) == 1
    assert manager.provides['no_provide'] == ['default_read', 'default_write']

def test_sequence_mismatched_provide(create_paths):
    """
    Thest that loading a sequence file with a mismatched provide statement raises
    the appropriate exception.
    """
    file_stem = 'provide_mismatch'
    with pytest.raises(CommandSequenceError,
        match='{} does not implement missing_sequence listed in its provided sequences'.format(file_stem)
    ):
        manager = CommandSequenceManager()
        paths = create_paths(['{}.py'.format(file_stem)])
        manager.load_module(paths)

def test_sequence_with_requires(create_paths):
    """
    Test that loading a sequence file with a requires statement correctly resolves the
    required module.
    """
    manager = CommandSequenceManager()
    paths = create_paths(['basic_sequences.py', 'with_requires.py'])
    manager.load_module(paths, False)
    manager.resolve()

    assert manager.requires['with_requires'] == ['basic_sequences']

def test_sequence_no_requires(create_paths):
    """
    Test that loading a sequence file without a requires statement correctly resolves to any
    empty requires value in the manager
    """
    manager = CommandSequenceManager()
    paths = create_paths(['basic_sequences.py'])
    manager.load_module(paths)

    assert manager.requires['basic_sequences'] == []

def test_sequence_missing_requires(create_paths):
    """
    Test that loading a sequence file with a requires statement but without the matching
    module raises an exception.
    """
    files = ['with_requires.py']
    with pytest.raises(
        CommandSequenceError, match='Failed to resolve required command sequence modules'
    ):
        manager = CommandSequenceManager()
        paths = create_paths(files)
        manager.load_module(paths)

def test_file_load_explicit_resolve(shared_datadir, create_paths):
    """
    Test that loading a single sequence module into a manager with an explicit resolve argument
    yields a correct initalised manager.
    """
    manager = CommandSequenceManager()
    paths = create_paths(['basic_sequences.py'])
    manager.load_module(paths)

    assert len(manager.modules) == 1
    assert 'basic_sequences' in manager.modules

def test_execute_sequence(create_paths):
    """
    Test that executing a sequence loaded from a file functions correctly, returning
    the appropriate value.
    """
    manager = CommandSequenceManager()
    paths = create_paths(['basic_sequences.py'])
    manager.load_module(paths)

    test_value = 90210
    ret_value = manager.execute('basic_return_value', test_value)

    assert ret_value == test_value

def test_execute_missing_sequence(create_paths):
    """
    Test that executing a missing sequence raises an exception correctly.
    the appropriate value.
    """
    manager = CommandSequenceManager()
    paths = create_paths(['basic_sequences.py'])
    manager.load_module(paths)
    missing_sequence = 'basic_missing'

    with pytest.raises(
        CommandSequenceError, match='Missing command sequence: {}'.format(missing_sequence)
    ):
        manager.execute(missing_sequence, 4567)

def test_add_context_to_manager(create_paths, context_object):
    """
    Test that adding an object to the context of a manager makes that object available.
    """
    manager = CommandSequenceManager()
    obj_name = 'context_object'
    manager.add_context(obj_name, context_object)

    assert obj_name in manager.context
    assert id(context_object) == id(manager._get_context(obj_name))
    assert manager._get_context(obj_name).value == context_object.value

def test_access_context_in_sequence(create_paths, context_object):
    """
    Test that accessing a context in a sequence works as as expected.
    """
    manager = CommandSequenceManager()
    paths = create_paths(['context_data/context_sequences.py'])
    manager.load_module(paths)
    obj_name = 'context_object'
    manager.add_context(obj_name, context_object)

    value = 3.141
    return_val = manager.context_access(value)

    assert return_val == value + 1

def test_get_missing_context_object(create_paths):
    """
    Test that attempting to access a missing context object raises an appropriate exception.
    """
    manager = CommandSequenceManager()
    paths = create_paths(['context_data/context_sequences.py'])
    manager.load_module(paths)
    obj_name = 'context_object'
    manager.add_context(obj_name, context_object)

    with pytest.raises(
        CommandSequenceError, match=r'Manager context does not contain \S+'
    ):
        manager.missing_context_obj()
