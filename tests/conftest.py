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
    return 'World Hello'""")

    with_dependency_module = shared_datadir.joinpath('with_dependency.py')
    with_dependency_module.write_text("""requires = ['test_reload']
provides = ['generate_message']

def generate_message():
    return 'Message: ' + get_message()""")

    return [test_reload_module, with_dependency_module]