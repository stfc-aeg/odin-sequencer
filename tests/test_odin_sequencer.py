#!/usr/bin/env python

"""Tests for odin_sequencer package."""

import pytest


from odin_sequencer import CommandSequenceManager


@pytest.fixture
def make_seq_manager(shared_datadir):
    """Factory test fixture that allows a sequence manager to be created with
    a particular file name or list of file names.
    """
    def _make_seq_manager(file_or_files):

        if isinstance(file_or_files, list):
            seq_file = [str(shared_datadir / name) for name in file_or_files]
        else:
            seq_file = str(shared_datadir / file_or_files)

        return CommandSequenceManager(seq_file)
    
    return _make_seq_manager
    

def test_empty_manager():
    """Test that a command sequence manager initialsed without any sequence files is empty."""
    manager = CommandSequenceManager()

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

