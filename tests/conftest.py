"""This module includes commonly used pytest fixtures that can be called from test functions."""

import pytest


@pytest.fixture
def create_tmp_module_files(shared_datadir):
    """
    Test fixture for creating temporary module files that can be used to test the
    detection mechanism of the file watcher.
    """

    test_reload_module = shared_datadir.joinpath('test_reload.py')
    test_reload_module.write_text("""provides = ['get_message']
def get_message():
    print('Executing get_message')
    return 'World Hello'""")

    with_dependency_module = shared_datadir.joinpath('with_dependency.py')
    with_dependency_module.write_text("""requires = ['test_reload']
provides = ['generate_message']

def generate_message():
    print('Executing generate_message')
    return 'Message: ' + get_message()""")

    return [test_reload_module, with_dependency_module]


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
