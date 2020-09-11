"""File watchers for odin-sequencer.

This module implements odin-sequencer file watchers that implement the IFileWatcher
interface. It also implements a file watcher factory that is responsible for creating
file watcher objects. The different file watcher classes allow for file modification
events to be detected and details about the modified file(s) to be retrieved. The
InotifyFileWatcher class uses the inotify library to register files for watching
and wait for notification events. The library is only compatible with linux systems
and to make sure that file modifications can still be detected on other systems, the
StandaloneFileWatcher class was implemented. This class does not use any file watching
libraries but instead compares the times a specific file was last modified.
"""
from abc import ABC, abstractmethod
import threading
import queue
import os

try:
    import inotify.adapters

    INOTIFY_IMPORTED = True
except (ImportError, OSError):
    INOTIFY_IMPORTED = False

from .exceptions import CommandSequenceError


class IFileWatcher(ABC):
    """
    An abstract class that defines the methods that file watcher concrete
    classes  should implement.
    """

    @abstractmethod
    def __init__(self):
        self.watched_files = None
        self.is_watching = False
        self.thread = None

    def run(self):
        """Run the watching process

        This method creates a thread and starts the watching process by executing
        the _run function from the relevant concrete class in the new thread.
        """
        if self.is_watching:
            raise CommandSequenceError(
                'File watcher has already been started'
            )

        self.thread = threading.Thread(target=self._run)
        # Daemon must be set to True to ensure that the created
        # thread stops when the main one is stopped
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the watching process

        This method stops the watching process by un-registering files
        from watching and setting self.is_watching to False.
        """
        if not self.is_watching:
            raise CommandSequenceError(
                'Cannot stop file watcher as it has not been started'
            )

        self.remove_watch(list(self.watched_files))
        self.is_watching = False
        self.thread.join()

    @abstractmethod
    def add_watch(self, path_or_paths):
        """
        Register file(s) for watching. The actual logic of this method
        is defined in the concrete classes that implement this class.
        """

    @abstractmethod
    def remove_watch(self, path_or_paths):
        """
        Un-register file(s) from watching. The actual logic of this method
        is defined in the concrete classes that implement this class.
        """


class InotifyFileWatcher(IFileWatcher):
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
        super().__init__()
        self.i = inotify.adapters.Inotify()
        self.watched_files = set()
        self.modified_files_queue = queue.Queue()

        if path_or_paths:
            self.add_watch(path_or_paths)
            self.run()

    def _run(self):
        """Watch for modification events

        This method waits for modification events from inotify and when it receives
        one, it puts the path of the file from where the event is coming from into
        the queue. It puts the path only if it is not already in the queue.
        """
        self.is_watching = True

        print("Inotify class - num of threads is: " + str(threading.active_count()))

        for event in self.i.event_gen():
            if not self.is_watching:
                # This solves the problem with a while loop not exiting
                # when self.is_watching is set to False. Returning
                # ensures that the thread exits.
                return

            if event is not None:
                (_, _, path, _) = event
                if path not in self.modified_files_queue.queue:
                    self.modified_files_queue.put(path)

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

            if path not in self.watched_files and os.path.exists(path):
                self.i.add_watch(path, inotify.constants.IN_MODIFY)
                self.watched_files.add(path)

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

            if path in self.watched_files:
                self.i.remove_watch(path)
                self.watched_files.remove(path)


class StandaloneFileWatcher(IFileWatcher):
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
        super().__init__()
        self.watched_files = {}
        self.modified_files_queue = queue.Queue()

        if path_or_paths:
            self.add_watch(path_or_paths)
            self.run()

    def _run(self):
        """Watch for file modifications

        This method constantly iterates through the list of watched files, comparing
        the modification file times of each file. If it detects that the new
        time is not equal to the one that it has stored in the self.watched_files
        dictionary, it puts the path of the file into the queue and updates the
        modification time in the dictionary.
        """
        self.is_watching = True

        print("Standalone class - num of threads is: " + str(threading.active_count()))

        while self.is_watching:
            for path, last_modified in list(self.watched_files.items()):
                modified = os.stat(path).st_mtime

                if last_modified != modified and path not in self.modified_files_queue.queue:
                    self.modified_files_queue.put(path)
                    self.watched_files[path] = modified

    def add_watch(self, path_or_paths):
        """Add file(s) for watching

        This method takes path or paths in form of Path objects or Strings
        and adds them to the self.watched_files dictionary.

        :param path_or_paths: path(s) to file(s) that need to be added
                                for watching
        """
        if not isinstance(path_or_paths, list):
            path_or_paths = [path_or_paths]

        for path in path_or_paths:
            if not isinstance(path, str):
                path = str(path)

            if path not in self.watched_files and os.path.exists(path):
                last_modified = os.stat(path).st_mtime
                self.watched_files[path] = last_modified

    def remove_watch(self, path_or_paths):
        """Remove file(s) from watching

        This method takes path or paths in form of Path objects or
        Strings and removes them from the self.watched_files dictionary.

        :param path_or_paths: path(s) to file(s) that need to be removed
                                from watching
        """
        if not isinstance(path_or_paths, list):
            path_or_paths = [path_or_paths]

        for path in path_or_paths:
            if not isinstance(path, str):
                path = str(path)

            if path in self.watched_files:
                del self.watched_files[path]


class FileWatcherFactory():
    """File watcher class factory.

    The class implements a file watcher factory that is responsible for creating
    file watcher objects.
    """

    # The file watcher classes that the factory can use to create objects
    __file_watcher_classes = {
        'inotify': InotifyFileWatcher,
        'standalone': StandaloneFileWatcher
    }

    @staticmethod
    def create_file_watcher(*args, name=None, **kwargs):
        """Create file watcher object.

        This method creates a file watcher object. It has an optional parameter that allows callers
        to specify the type of file watcher object that they require to be created. Alternatively,
        if no name is provided, then the factory checks whether the inotify library was imported or
        not, to decide the type of file watcher object that it needs to create.

        :param name: name of the file watcher to be created (default None)
        """

        if name:
            if name == 'inotify' and not INOTIFY_IMPORTED:
                raise CommandSequenceError('The requested file watcher cannot be created because '
                                           'the inotify module could not be found')

            file_watcher_class = FileWatcherFactory.__file_watcher_classes.get(name.lower(), None)
        else:
            if INOTIFY_IMPORTED:
                file_watcher_class = FileWatcherFactory.__file_watcher_classes.get('inotify', None)
            else:
                file_watcher_class = FileWatcherFactory.__file_watcher_classes.get(
                    'standalone', None)

        if file_watcher_class:
            return file_watcher_class(*args, **kwargs)
        raise CommandSequenceError('The requested file watcher cannot be created because it has '
                                   'not been implemented')
