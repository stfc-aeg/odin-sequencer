"""File watcher for ODIN control systems.

This module implements a file watcher for ODIN-based control systems. This allows for file
modification events to be detected and details about the modified file(s) to be retrieved.
"""
import sys
from pathlib import Path
import threading
import queue
import os

try:
    import inotify.adapters
    inotify_imported = True
except ImportError:
    inotify_imported = False

class FileWatcher:
    """
    File watcher class.

    The class implements a file watcher, which allows one or more files to be watched
    for modification events, and details of the modified file(s) to be retrieved.
    """

    def __init__(self, path_or_paths=None):
        """Initialise the file watcher.

        This method initialises the file watcher, optionally watching one or more files.

        :param path_or_paths: path(s) to file(s) that require watching
        """
        if inotify_imported:
            self._i = inotify.adapters.Inotify()
            self._watched_files = set()
        else:
            self._watched_files = {}
        
        self._thread = None
        self._is_watching = False
        self.modified_files_queue = queue.Queue()
        
        if path_or_paths:
            self.add_watch(path_or_paths)
            self.run()

    def run(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def _run(self):
        self._is_watching = True

        print (threading.active_count())

        if inotify_imported:
            for event in self._i.event_gen():
                if not self._is_watching:
                    return

                if event is not None:
                    (_, type_names, path, filename) = event
                    print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(
                            path, filename, type_names))
                    self.modified_files_queue.put(Path(path))
        else:
            while self._is_watching:
                for path, last_modified in list(self._watched_files.items()):
                    modified = os.stat(path).st_mtime
                    if last_modified != modified:
                        self.modified_files_queue.put(Path(path))
                        self._watched_files[path] = modified

    def stop(self):
        self.remove_watch(list(self._watched_files))
        self._is_watching = False
        self._thread.join()
    
    def add_watch(self, path_or_paths):
        if not isinstance(path_or_paths, list):
            path_or_paths = [path_or_paths]

        for path in path_or_paths:
            if not isinstance(path, str):
                path = str(path)

            if path not in self._watched_files:
                if inotify_imported:
                    self._i.add_watch(path, inotify.constants.IN_MODIFY)
                    self._watched_files.add(path)
                else:
                    last_modified = os.stat(path).st_mtime
                    self._watched_files[path] = last_modified

    def remove_watch(self, path_or_paths):
        if not isinstance(path_or_paths, list):
            path_or_paths = [path_or_paths]

        for path in path_or_paths:
            if not isinstance(path, str):
                path = str(path)

            if path in self._watched_files:
                if inotify_imported:
                    print("Removing: " + path)
                    self._i.remove_watch(path)
                    self._watched_files.remove(path)
                else:
                    del(self._watched_files[path])