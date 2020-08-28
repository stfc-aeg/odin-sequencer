import threading
import queue
import os
import inotify.adapters

from .exceptions import CommandSequenceError

class InotifyFileWatcher:
    """File watcher class.

    The class implements a file watcher, which allows one or more files to be watched
    for modification events, and details of the modified file(s) to be retrieved. It
    uses the inotify library to register files for watching and wait for notification
    events.
    """

    def __init__(self, path_or_paths=None):
        """Initialise the file watcher.

        This method initialises the file watcher, optionally watching one or more files.

        :param path_or_paths: path(s) to file(s) that require watching (default None)
        """
        self._i = inotify.adapters.Inotify()
        self._watched_files = set()
        self._thread = None
        self._is_watching = False
        self.modified_files_queue = queue.Queue()

        if path_or_paths:
            self.add_watch(path_or_paths)
            self.run()

    def run(self):
        """Run the watching process

        This method creates a thread and starts the watching process
        by executing the _run function in the new thread.
        """
        if self._is_watching:
            raise CommandSequenceError(
                'File watcher has already been started'
            )

        self._thread = threading.Thread(target=self._run)
        # Daemon must be set to True to ensure that the created
        # thread stops when the main one is stopped
        self._thread.daemon = True
        self._thread.start()

    def _run(self):
        """Watch for modification events

        This method waits for modification events from inotify and when it receives
        one, it puts the path of the file from where the event is coming from into
        the queue. It puts the path only if it is not already in the queue.
        """
        self._is_watching = True

        for event in self._i.event_gen():
            if not self._is_watching:
                # This solves the problem with a while loop not exiting
                # when self._is_watching is set to False. Returning
                # ensures that the thread exits.
                return

            if event is not None:
                (_, _, path, _) = event
                if path not in self.modified_files_queue.queue:
                    self.modified_files_queue.put(path)

    def stop(self):
        """Stop the watching process

        This method stops the watching process by un-registering files
        from watching and setting self._is_watching to False.
        """
        if not self._is_watching:
            raise CommandSequenceError(
                'Cannot stop file watcher as it has not been started'
            )

        self.remove_watch(list(self._watched_files))
        self._is_watching = False
        self._thread.join()

    def add_watch(self, path_or_paths):
        """Register file(s) for watching

        This method takes path or paths in form of Path objects or Strings
        and registers them with inotify for watching of modification evenets.

        :param path_or_paths: path(s) to file(s) that need to be registered
                                for watching
        """
        if not isinstance(path_or_paths, list):
            path_or_paths = [path_or_paths]

        for path in path_or_paths:
            if not isinstance(path, str):
                path = str(path)

            if path not in self._watched_files and os.path.exists(path):
                self._i.add_watch(path, inotify.constants.IN_MODIFY)
                self._watched_files.add(path)

    def remove_watch(self, path_or_paths):
        """Un-register file(s) from watching

        This method takes path or paths in form of Path objects or
        Strings and un-registers them from inotify from watching of
        modification events.

        :param path_or_paths: path(s) to file(s) that need to be un-registered
                                from watching
        """
        if not isinstance(path_or_paths, list):
            path_or_paths = [path_or_paths]

        for path in path_or_paths:
            if not isinstance(path, str):
                path = str(path)

            if path in self._watched_files:
                self._i.remove_watch(path)
                self._watched_files.remove(path)


class StandaloneFileWatcher:
    """File watcher class.

    The class implements a file watcher, which allows one or more files to be watched
    for modification events, and details of the modified file(s) to be retrieved. It
    does not use any file watching libraries but instead it constantly iterates through
    the files that it watches and compares the last modification files of each file.
    """

    def __init__(self, path_or_paths=None):
        """Initialise the file watcher.

        This method initialises the file watcher, optionally watching one or more files.

        :param path_or_paths: path(s) to file(s) that require watching (default None)
        """
        self._watched_files = {}
        self._thread = None
        self._is_watching = False
        self.modified_files_queue = queue.Queue()

        if path_or_paths:
            self.add_watch(path_or_paths)
            self.run()

    def run(self):
        """Run the watching process

        This method creates a thread and starts the watching process
        by executing the _run function in the new thread.
        """
        if self._is_watching:
            raise CommandSequenceError(
                'File watcher has already been started'
            )

        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()

    def _run(self):
        """Watch for file modifications

        This method constantly iterates through the list of watched files, comparing
        the modification file times of each file. If it detects that the new
        time is not equal to the one that it has stored in the self._watched_files
        dictionary, it puts the path of the file into the queue and updates the
        modification time in the dictionary.
        """
        self._is_watching = True

        while self._is_watching:
            for path, last_modified in list(self._watched_files.items()):
                modified = os.stat(path).st_mtime

                if last_modified != modified and path not in self.modified_files_queue.queue:
                    self.modified_files_queue.put(path)
                    self._watched_files[path] = modified

    def stop(self):
        if not self._is_watching:
            raise CommandSequenceError(
                'Cannot stop file watcher as it has not been started'
            )

        self.remove_watch(list(self._watched_files))
        # Daemon must be set to True to ensure that the created
        # thread stops when the main one is stopped
        self._is_watching = False
        self._thread.join()

    def add_watch(self, path_or_paths):
        """Add file(s) for watching

        This method takes path or paths in form of Path objects or Strings
        and adds them to the self._watched_files dictionary.

        :param path_or_paths: path(s) to file(s) that need to be added
                                for watching
        """
        if not isinstance(path_or_paths, list):
            path_or_paths = [path_or_paths]

        for path in path_or_paths:
            if not isinstance(path, str):
                path = str(path)

            if path not in self._watched_files and os.path.exists(path):
                last_modified = os.stat(path).st_mtime
                self._watched_files[path] = last_modified

    def remove_watch(self, path_or_paths):
        """Remove file(s) from watching

        This method takes path or paths in form of Path objects or
        Strings and removes them from the self._watched_files dictionary.

        :param path_or_paths: path(s) to file(s) that need to be removed
                                from watching
        """
        if not isinstance(path_or_paths, list):
            path_or_paths = [path_or_paths]

        for path in path_or_paths:
            if not isinstance(path, str):
                path = str(path)

            if path in self._watched_files:
                del (self._watched_files[path])