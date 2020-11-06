"""Test utilities

This module includes various methods that help in writing the tests.
It should not be imported by any module except for test code.
"""

import time
import os


def modify_test_reload_module_file(shared_datadir):
    """
    This method modifies the content of the test_reload.py module.
    There is a small delay to ensure that the modification does not
    happen at the same time as the creation of the module.
    """
    time.sleep(0.1)
    module = shared_datadir.joinpath('test_reload.py')

    module.write_text("""provides = ['get_message', 'basic_sequence']
def get_message():
    return 'Hello World'

def basic_sequence(value=[1]):
    return value""")


def modify_test_reload_module_file_syntax_error(shared_datadir):
    time.sleep(0.1)
    module = shared_datadir.joinpath('test_reload.py')

    module.write_text("""provides = ['get_message', 'basic_sequence']
dof get_message():
    return 'Hello World'
 
def basic_sequence(value=[1]):
    return value""")


def modify_with_dependency_module_file(shared_datadir):
    """
    This method modifies the content of the with_dependency.py module.
    There is a small delay to ensure that the modification does not
    happen at the same time as the creation of the module.
    """
    time.sleep(0.1)
    module = shared_datadir.joinpath('with_dependency.py')

    module.write_text("""requires = ['test_reload']
provides = ['generate_message']

def generate_message():
    return 'Message: ' + get_message() + ' - ' + get_message()""")


def await_queue_size(module_watcher, expected_queue_size):
    """
    This method Waits for the size of the queue to reach the given expected queue
    size number. The loop exists if the number is not reached after 15 seconds.
    param manager: manager object from where the module watcher and its queue can be acccessed
    param expected_queue_size: the size that the queue needs to reach.
    """
    for _ in range(30, 0, -1):
        if module_watcher.modified_files_queue.qsize() == expected_queue_size:
            break
        time.sleep(0.5)


def get_last_modified_file_time(path):
    """This method gets the time that the given file was last modified.
    :param path: the path to the file
    """
    return os.stat(path).st_mtime


def was_file_modified(path, last_modified_time):
    """This method checks whether the given file was modified.

    :param path: the path to the file
    :param last_modified_time: the time the file was last modified
    :return: return False if modification did not occur after 15 seconds,
                otherwise return True
    """
    for _ in range(30, 0, -1):
        modified_time = get_last_modified_file_time(path)
        if modified_time != last_modified_time:
            return True

        time.sleep(0.5)

    return False
