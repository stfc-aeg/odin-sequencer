"""Test utilities

This module includes various methods that help in writing the tests.
It should not be imported by any module except for test code.
"""

import time
import os


def modify_test_reload_module_file(shared_datadir):
    """This method modifies the content of the test_reload.py module"""
    time.sleep(0.1)
    module = shared_datadir.joinpath('test_reload.py')

    module.write_text("""provides = ['get_message']
def get_message():
    return 'Hello World'""")


def modify_with_dependency_module_file(shared_datadir):
    """This method modifies the content of the with_dependency.py module"""
    time.sleep(0.1)
    module = shared_datadir.joinpath('with_dependency.py')

    module.write_text("""requires = ['test_reload']
provides = ['generate_message']

def generate_message():
    return 'Message: ' + get_message() + ' - ' + get_message()""")


def await_queue_size(file_watcher, expected_queue_size):
    """
    This method Waits for the size of the queue to reach the given expected queue
    size number. The loop exists if the number is not reached after 10 seconds.
    """

    for i in range(60, 0, -1):
        actual_queue_size = file_watcher.modified_files_queue.qsize()
        print("i = {}, expected_queue_size = {}, actual_queue_size = {}".format(
            i, str(expected_queue_size), str(actual_queue_size)))

        if actual_queue_size == expected_queue_size:
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
    for i in range(60, 0, -1):
        modified_time = get_last_modified_file_time(path)
        print("i = {}, last_modified_time = {}, modified_time = {}".format(
            i, str(last_modified_time), str(modified_time)))

        if modified_time != last_modified_time:
            return True
        time.sleep(0.5)

    return False
