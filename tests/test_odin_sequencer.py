#!/usr/bin/env python

"""Tests for odin_sequencer package."""

import pytest

from odin_sequencer import CommandSequenceManager, CommandSequenceError

@pytest.fixture
def make_seq_manager(shared_datadir):
    """
    Factory test fixture that allows a sequence manager to be created with
    a particular file name or list of file names.
    """
    def _make_seq_manager(file_or_files=None):

        if not file_or_files:
            seq_file = None
        elif isinstance(file_or_files, list):
            seq_file = [str(shared_datadir / name) for name in file_or_files]
        else:
            seq_file = str(shared_datadir / file_or_files)

        return CommandSequenceManager(seq_file)
    
    return _make_seq_manager
    

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

def test_empty_manager(make_seq_manager):
    """Test that a command sequence manager initialsed without any sequence files is empty."""
    manager = make_seq_manager()

    assert len(manager.modules) == 0
    assert len(manager.provides) == 0
    assert len(manager.requires) == 0
    assert len(manager.context) == 0

def test_basic_manager_loaded(make_seq_manager):
    """
    Test that a command sequence manager initialised with a single file exposes the
    correct sequence functions.
    """
    manager = make_seq_manager('basic_sequences.py')

    assert len(manager.modules) == 1
    assert len(manager.provides) == 1
    assert len(manager.requires) == 1
    assert hasattr(manager, 'basic_read')
    assert hasattr(manager, 'basic_write')

def test_load_module_with_illegal_syntax(make_seq_manager):
    """
    Test that loading a sequence module with illegal python synax raises an error
    appropriately.
    """
    file_name = 'illegal_syntax.py'
    with pytest.raises(
        CommandSequenceError, match=r'Syntax error loading .*\/{}'.format(file_name)
    ):
        make_seq_manager(file_name)

def test_load_module_with_bad_import(make_seq_manager):
    """
    Test that loading a module with a bad import statement raises an error
    appropriately.
    """
    file_name = 'illegal_import.py'
    with pytest.raises(
        CommandSequenceError, match=r'Import error loading .*\/{}'.format(file_name)
    ):
        make_seq_manager(file_name)

def test_load_missing_module(make_seq_manager):
    """
    Test that loading a missing sequence module file into a manager raises an error
    appropriately.
    """
    file_name = 'does_not_exist.py'
    with pytest.raises(
        CommandSequenceError, match=r'Sequence module file .*\/{} not found'.format(file_name)
    ):
        make_seq_manager(file_name)

def test_manager_multiple_files(make_seq_manager):

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
    This that loading a sequence file with a mismatched provide statement raises
    the appropriate exception.
    """
    file_stem = 'provide_mismatch'
    with pytest.raises(CommandSequenceError,
        match='{} does not implement missing_sequence listed in its provided sequences'.format(file_stem)
    ):
        make_seq_manager('{}.py'.format(file_stem))


def test_sequence_with_requires(make_seq_manager):
    """
    Test that loading a sequence file with a requires statement correctly resolves the
    required module.
    """
    files = ['basic_sequences.py', 'with_requires.py']
    manager = make_seq_manager(files)

    assert manager.requires['with_requires'] == ['basic_sequences']

def test_sequence_no_requires(make_seq_manager):
    """
    Test that loading a sequence file without a requires statement correctly resolves to any
    empty requires value in the manager
    """
    files = ['basic_sequences.py']
    manager = make_seq_manager(files)

    assert manager.requires['basic_sequences'] == []

def test_sequence_missing_requires(make_seq_manager):
    """
    Test that loading a sequence file with a requires statement but without the matching
    module raises an exception.
    """
    files = ['with_requires.py']
    with pytest.raises(
        CommandSequenceError, match='Failed to resolve required command sequence modules'
    ):
        make_seq_manager(files)

def test_file_load_explicit_resolve(shared_datadir, make_seq_manager):
    """
    Test that loading a single sequence module into a manager with an explicit resolve argument
    yeilds a correct initalised manager.
    """
    manager = make_seq_manager()
    manager.load_module(str(shared_datadir / 'basic_sequences.py'))

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
    manager = make_seq_manager('context_sequences.py')
    obj_name = 'context_object'
    manager.add_context(obj_name, context_object)

    value = 3.141
    return_val = manager.context_access(value)

    assert return_val == value + 1

def test_get_missing_context_object(make_seq_manager):
    """
    Test that attempting to access a missing context object raises an appropriate exception.
    """
    manager = make_seq_manager('context_sequences.py')
    obj_name = 'context_object'
    manager.add_context(obj_name, context_object)

    with pytest.raises(
        CommandSequenceError, match=r'Manager context does not contain \S+'
    ):
        manager.missing_context_obj()
