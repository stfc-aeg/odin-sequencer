"""Process Queue adapter for ODIN sequencer 

This class implements an adapter used for adding a process writer context and starts
process monitor for the odin sequencer.

Rhys Evans, STFC
"""
import logging
from celery import group, signature

from odin_sequencer.process_queue import process_queue, process_monitor
from odin_sequencer.tasks import *

from odin.adapters.adapter import ApiAdapter


class ProcessQueueContextAdapter(ApiAdapter):
    """Process Queue Context context adapter class for the ODIN server.

    This adapter provides a Process Writer context and starts the process monitor
    for the odin sequencer.
    """

    def __init__(self, **kwargs):
        """Initialize the ProcessQueueContextAdapter object.

        This constructor initializes the ProcessQueueContextAdapter object.

        :param kwargs: keyword arguments specifying options
        """
        # Intialise superclass
        super(ProcessQueueContextAdapter, self).__init__(**kwargs)

        self.adapters = {}

        logging.debug('ProcessQueueContextAdapter loaded')

    def initialize(self, adapters):
        """Initialize the ondin sequencer adapter after it has been loaded and added ProcessWriter 
        context to sequencer.

        Receive a dictionary of all loaded adapters so that they may be accessed by this adapter.
        Remove itself from the dictionary so that it does not reference itself, as doing so
        could end with an endless recursive loop.
        """

        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        logging.debug("Received following dict of Adapters: %s", self.adapters)
        
        process_writer = ProcessWriter()
        self.adapters['odin_sequencer'].add_context('process_writer', process_writer)
        logging.debug("Process writer context added to odin sequencer.")

        self.adapters['odin_sequencer'].start_process_monitor(process_monitor)
        logging.debug("Process monitor started for odin sequencer.")


class ProcessWriter():
    """ ApiAdapter for the Command Sequencer.

    Adapter which exposes the underlying Command Sequencer.
    """

    def run(self, function, ignore_result, *args):
        """This method calls the celery task _run with the given function name and arguments.
        :param function: Name of function from 'tasks.py'
        :param *args: Arguments for the given function
        """
        logging.debug(args)
        return self._run.apply_async(args=(function, args), ignore_results=ignore_result)

    def group(self, function, ignore_result, iterator, *args):
        """This method calls a group of celery task _run with the given function name and arguments.
        :param function: Name of function from 'tasks.py'
        :param iterator: Iterator for the group function
        """
        signatures = []
        for i in iterator:
            signatures.append(
                self._run.signature(
                    args=(
                        function, 
                        self.list_append([i], *args) if args else [i]
                    ),
                )
            )
        task_group = group(signatures)
        return task_group.apply_async(ignore_results = ignore_result)

    @process_queue.task(bind=True)
    def _run(self, function, args):
        """This method runs the given function with the given arguments.
        :param function: Name of function from 'tasks.py'
        :param args: Arguments for the given function
        # """
        group_uuid = self.request.group if self.request.group else None
        task_uuid = self.request.id

        if group_uuid:
            self.send_event(
                'started-group-task', 
                task_uuid = task_uuid, 
                task_name = function, 
                group_uuid = group_uuid
            )
        else:
            self.send_event(
                'started-task', 
                task_uuid = task_uuid,
                task_name = function
            )
        
        try:
            result = globals()[function](*args)
            if group_uuid:
                self.send_event(
                    'successful-group-task', 
                    task_uuid = task_uuid, 
                    task_name = function, 
                    group_uuid = group_uuid
                )
            else:
                self.send_event(
                    'successful-task', 
                    task_uuid = task_uuid, 
                    task_name = function
                )
        except Exception as e:
            if group_uuid:
                self.send_event(
                    'failed-group-task', 
                    task_uuid = task_uuid, 
                    task_name = function, 
                    group_uuid = group_uuid
                )
            else:
                self.send_event(
                    'failed-task', 
                    task_uuid = task_uuid, 
                    task_name = function
                )
            raise e

    def list_append(self, lst, item):
        """This method returns the given list with item appened.
        :param lst: initial list
        :param item: item to be appened to lst
        """
        lst.append(item)
        return lst