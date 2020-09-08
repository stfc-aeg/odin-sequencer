"""Tests for InotifyFileWatcher class

Some tests use the was_file_modified or await_queue_size method to ensure that
a file was modified or that the file watcher, which runs in a separate thread,
detects and puts details of the modified files into the queue before the assertions
happen. Some tests also stop the file watcher if it has been started to ensure that
the separate thread on which the file watcher runs is stopped.
"""

import pytest
from odin_sequencer import StandaloneFileWatcher, CommandSequenceError
from .testutils import (modify_test_reload_module_file, modify_with_dependency_module_file,
                        await_queue_size, get_last_modified_file_time, was_file_modified)

@pytest.fixture
def make_file_watcher():
    """Test fixture for creating StandaloneFileWatcher object"""

    def _make_file_watcher(path_or_paths=None):
        return StandaloneFileWatcher(path_or_paths)

    return _make_file_watcher


def test_add_watch_with_file_path(make_file_watcher, create_tmp_module_files):
    """
    Test that a path (in form of a Path object) to a specific file is added
    to be watched.
    """
    module = create_tmp_module_files[0]
    file_watcher = make_file_watcher()
    file_watcher.add_watch(module)

    assert len(file_watcher._watched_files) == 1


def test_add_watch_with_multiple_file_paths(make_file_watcher, create_tmp_module_files):
    """
    Test that paths (in form of Path objects) to specific files are added to be
    watched.
    """
    tmp_files = create_tmp_module_files
    file_watcher = make_file_watcher()

    file_watcher.add_watch(tmp_files)

    assert len(file_watcher._watched_files) == len(tmp_files)
    assert str(tmp_files[0]) in file_watcher._watched_files
    assert str(tmp_files[1]) in file_watcher._watched_files


def test_add_watch_with_file_path_as_string(make_file_watcher, create_tmp_module_files):
    """
    Test that a path (in form of a String) to a specific file is added to be
    watched.
    """
    module = str(create_tmp_module_files[0])
    file_watcher = make_file_watcher()

    file_watcher.add_watch(module)

    assert len(file_watcher._watched_files) == 1
    assert module in file_watcher._watched_files


def test_add_watch_with_missing_file_path(make_file_watcher, shared_datadir):
    """Test that a path to a missing file is not added to be watched."""
    file_watcher = make_file_watcher()

    file_watcher.add_watch(shared_datadir.joinpath('does_not_exist.py'))

    assert len(file_watcher._watched_files) == 0


def test_add_watch_with_path_to_already_watched_file(make_file_watcher, create_tmp_module_files):
    """Test that a path to an already watched file is not added to be watched again."""
    module = create_tmp_module_files[0]
    file_watcher = make_file_watcher()

    file_watcher.add_watch(module)
    file_watcher.add_watch(module)

    assert len(file_watcher._watched_files) == 1


def test_remove_watch_with_file_path(make_file_watcher, create_tmp_module_files):
    """
    Test that a path (in form of a Path object) to a watched file is removed from
    watching.
    """
    tmp_files = create_tmp_module_files
    file_watcher = make_file_watcher()
    file_watcher.add_watch(tmp_files)

    file_watcher.remove_watch(tmp_files[0])

    assert str(tmp_files[0]) not in file_watcher._watched_files
    assert len(file_watcher._watched_files) == len(tmp_files) - 1


def test_remove_watch_with_multiple_file_paths(make_file_watcher, create_tmp_module_files):
    """
    Test that paths (in form of Path objects) to watched files are removed from
    watching.
    """
    tmp_files = create_tmp_module_files
    file_watcher = make_file_watcher()
    file_watcher.add_watch(tmp_files)

    file_watcher.remove_watch(tmp_files)

    assert str(tmp_files[0]) not in file_watcher._watched_files
    assert str(tmp_files[1]) not in file_watcher._watched_files
    assert len(file_watcher._watched_files) == 0


def test_remove_watch_with_file_path_as_string(make_file_watcher, create_tmp_module_files):
    """
    Test that a path (in form of a String) to a specific file is removed from
    watching.
    """
    tmp_files = create_tmp_module_files
    file_watcher = make_file_watcher()
    file_watcher.add_watch(tmp_files)

    file_watcher.remove_watch(str(tmp_files[0]))

    assert str(tmp_files[0]) not in file_watcher._watched_files
    assert len(file_watcher._watched_files) == len(tmp_files) - 1


def test_remove_watch_with_not_watched_file_path(make_file_watcher, create_tmp_module_files):
    """
    Test that a path to a non-watched file is not attempted to be removed from
    watching.
    """
    module = create_tmp_module_files[0]
    file_watcher = make_file_watcher()

    file_watcher.remove_watch(module)

    assert len(file_watcher._watched_files) == 0


def test_stop_when_file_watcher_is_not_started(make_file_watcher):
    """
    Test that stopping the file watcher when it has not previously
    been tarted raises an error appropriately.
    """
    file_watcher = make_file_watcher()

    with pytest.raises(
            CommandSequenceError, match='Cannot stop file watcher as it has not been started'
    ):
        file_watcher.stop()


def test_stop_when_file_watcher_is_started(make_file_watcher, create_tmp_module_files):
    """
    Test that the file watcher can be successfully stopped when it has previously been
    started.
    """
    tmp_files = create_tmp_module_files
    file_watcher = make_file_watcher(tmp_files)

    file_watcher.stop()

    assert len(file_watcher._watched_files) == 0
    assert file_watcher._is_watching is False


def test_run_when_file_watcher_is_started(make_file_watcher, create_tmp_module_files):
    """
    Test that starting the file watcher when it has previously been started raises
    an error appropriately.
    """
    tmp_files = create_tmp_module_files
    file_watcher = make_file_watcher(tmp_files)

    with pytest.raises(
            CommandSequenceError, match='File watcher has already been started'
    ):
        file_watcher.run()

    file_watcher.stop()


def test_empty_file_watcher(make_file_watcher, create_tmp_module_files):
    """
    Test that a file watcher initialised without any paths to files has
    an empty watch list and does not start the watching process.
    """
    file_watcher = make_file_watcher()

    assert file_watcher._thread is None
    assert len(file_watcher._watched_files) == 0
    assert file_watcher._is_watching is False


def test_basic_file_watcher(make_file_watcher, create_tmp_module_files):
    """
    Test that a file watcher initialised with a single path adds the
    path to the watch list and starts the watching process.
    """
    module = create_tmp_module_files[0]
    file_watcher = make_file_watcher(module)

    assert file_watcher._thread is not None
    assert len(file_watcher._watched_files) == 1
    assert file_watcher._is_watching is True

    file_watcher.stop()


def test_file_watcher_when_watched_file_is_modified(shared_datadir, make_file_watcher,
                                                    create_tmp_module_files):
    """
    Test that the file watcher successfully detects modification events when a watched
    file is modified and that it successfully puts the path to that file into the queue.
    """
    tmp_files = create_tmp_module_files
    file_watcher = make_file_watcher(tmp_files)

    modify_test_reload_module_file(shared_datadir)
    await_queue_size(file_watcher, 1)

    assert file_watcher.modified_files_queue.qsize() == 1

    file_watcher.stop()


def test_file_watcher_when_multiple_watched_files_are_modified(shared_datadir, make_file_watcher,
                                                               create_tmp_module_files):
    """
    Test that the file watcher successfully detects modification events when watched files
    are modified and that it successfully puts the paths to those files into the queue.
    """
    tmp_files = create_tmp_module_files
    file_watcher = make_file_watcher(tmp_files)

    modify_test_reload_module_file(shared_datadir)
    modify_with_dependency_module_file(shared_datadir)
    await_queue_size(file_watcher, 2)

    assert file_watcher.modified_files_queue.qsize() == 2

    file_watcher.stop()


def test_file_watcher_when_non_watched_file_is_modified(shared_datadir, make_file_watcher,
                                                        create_tmp_module_files):
    """
    Test that the file watcher does not detect modification events when a non-watched
    file is modified and that it does not put the path to that file into the queue.
    """
    tmp_files = create_tmp_module_files
    test_reload_module = tmp_files[0]
    with_dependency_module = tmp_files[1]
    last_modified_time = get_last_modified_file_time(with_dependency_module)
    file_watcher = make_file_watcher(test_reload_module)

    modify_with_dependency_module_file(shared_datadir)
    file_modified = was_file_modified(with_dependency_module, last_modified_time)

    if file_modified:
        assert file_watcher.modified_files_queue.empty() is True
    else:
        pytest.fail()

    file_watcher.stop()


def test_file_watcher_when_previously_watched_file_is_modified(shared_datadir, make_file_watcher,
                                                               create_tmp_module_files):
    """
    Test that the file watcher does not detect modification events when a previously watched
    file is modified and that it does not put the path to that file into the queue.
    """
    tmp_files = create_tmp_module_files
    test_reload_module = create_tmp_module_files[0]
    last_modified_time = get_last_modified_file_time(test_reload_module)
    file_watcher = make_file_watcher(tmp_files)

    file_watcher.remove_watch(test_reload_module)
    modify_test_reload_module_file(shared_datadir)
    file_modified = was_file_modified(test_reload_module, last_modified_time)

    if file_modified:
        assert file_watcher.modified_files_queue.empty() is True
    else:
        pytest.fail()

    file_watcher.stop()
