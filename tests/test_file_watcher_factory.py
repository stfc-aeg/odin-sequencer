""" Tests for FileWatcherFactory class

Some tests stop the file watcher if it has been started to ensure that
the separate thread on which the file watcher runs is stopped.
"""

import pytest
from odin_sequencer import FileWatcherFactory, InotifyFileWatcher, StandaloneFileWatcher, CommandSequenceError
import odin_sequencer.watcher as watcher


def test_create_file_watcher_with_inotify_as_name_without_paths():
    """
    Test that an Inotify file watcher is created when the string value
    inotify is passed to the create method of the factory class. Ensure
    that the file watching process is not started when paths are not
    passed to it.
    """
    file_watcher = FileWatcherFactory.create_file_watcher('inotify')

    assert isinstance(file_watcher, InotifyFileWatcher)
    assert file_watcher._thread is None
    assert len(file_watcher._watched_files) == 0
    assert file_watcher._is_watching is False


def test_create_file_watcher_with_inotify_as_name_with_paths(shared_datadir):
    """
    Test that an Inotify file watcher is created when the string value
    inotify is passed to the create method of the factory class. Ensure
    that the file watching process is  started when paths are passed to it.
    """
    files = [shared_datadir.joinpath('basic_sequences.py'), shared_datadir.joinpath('with_requires.py')]
    file_watcher = FileWatcherFactory.create_file_watcher(name='inotify', path_or_paths=files)

    assert isinstance(file_watcher, InotifyFileWatcher)
    assert file_watcher._thread is not None
    assert len(file_watcher._watched_files) == len(files)
    assert file_watcher._is_watching is True

    file_watcher.stop()


def test_create_file_watcher_with_standalone_as_name_without_paths():
    """
    Test that a Standalone file watcher is created when the string value
    standalone is passed to the create method of the factory class. Ensure
    that the file watching process is not started when paths are not
    passed to it.
    """
    file_watcher = FileWatcherFactory.create_file_watcher('standalone')

    assert isinstance(file_watcher, StandaloneFileWatcher)
    assert file_watcher._thread is None
    assert len(file_watcher._watched_files) == 0
    assert file_watcher._is_watching is False


def test_create_file_watcher_with_standalone_as_name_with_paths(shared_datadir):
    """
    Test that a Standalone file watcher is created when the string value
    standalone is passed to the create method of the factory class. Ensure
    that the file watching process is started when paths are passed to it.
    """
    files = [shared_datadir.joinpath('basic_sequences.py'), shared_datadir.joinpath('with_requires.py')]
    file_watcher = FileWatcherFactory.create_file_watcher(name='standalone', path_or_paths=files)

    assert isinstance(file_watcher, StandaloneFileWatcher)
    assert file_watcher._thread is not None
    assert len(file_watcher._watched_files) == len(files)
    assert file_watcher._is_watching is True

    file_watcher.stop()


def test_create_file_watcher_with_not_implemented_name():
    """
    Test that passing an invalid string value to the create method of the
    factory class raises an error appropriately.
    """
    with pytest.raises(
        CommandSequenceError, match='The requested file watcher cannot be created because it has '
                                    'not been implemented'
    ):
        FileWatcherFactory.create_file_watcher('notimplemented')


def test_create_file_watcher_with_inotify_imported_and_no_name():
    """
    Test that an Inotify file watcher is created when no string value
    is provided but the import of the inotify library was successful.
    """
    file_watcher = FileWatcherFactory.create_file_watcher()

    assert isinstance(file_watcher, InotifyFileWatcher)


def test_create_file_watcher_without_inotify_imported_and_name():
    """
    Test that a Standalone file watcher is created when no string value
    is provided but the import of the inotify library was not successful.
    """
    watcher.inotify_imported = False
    file_watcher = FileWatcherFactory.create_file_watcher()

    assert isinstance(file_watcher, StandaloneFileWatcher)


def test_create_file_watcher_with_inotify_as_name_and_without_inotify_imported():
    """
    Test that trying to create an Inotify file watcher when the import of
    the inotify library was not successful raises an error appropriately.
    """
    watcher.inotify_imported = False

    with pytest.raises(
        CommandSequenceError, match='The requested file watcher cannot be created '
                                    'because the inotify module could not be found'
    ):
        FileWatcherFactory.create_file_watcher('inotify')
