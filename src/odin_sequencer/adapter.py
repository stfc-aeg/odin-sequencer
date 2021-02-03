"""Command sequence manager adapter

Adapter which exposes the underlying Command sequence manager module

Viktor Bozhinov, STFC.
"""
import logging

from tornado.escape import json_decode
from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types

from odin_sequencer import CommandSequenceError
from .command_sequencer import CommandSequencer


class CommandSequenceManagerAdapter(ApiAdapter):
    """ ApiAdapter for the Command Sequencer.

    Adapter which exposes the underlying Command Sequencer.
    """

    def __init__(self, **kwargs):
        """Initialise the CommandSequenceManagerAdapter object.

        This constructor initialises the CommandSequenceManagerAdapter object.
        :param kwargs: keyword arguments specifying options
        """
        # Initialise superclass
        super(CommandSequenceManagerAdapter, self).__init__(**kwargs)

        # Parse options
        sequence_location = (self.options.get('sequence_location'))

        self.command_sequencer = CommandSequencer(sequence_location)
        logging.debug('CommandSequenceManagerAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object

        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.command_sequencer.get(path)
            status_code = 200
        except CommandSequenceError as error:
            response = {'error': str(error)}
            status_code = 400

        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            data = json_decode(request.body)
            self.command_sequencer.set(path, data)
            response = self.command_sequencer.get(path)
            status_code = 200
        except CommandSequenceError as error:
            response = {'error': str(error)}
            status_code = 400
        except (TypeError, ValueError) as error:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(error))}
            status_code = 400

        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def add_context(self, name, obj):
        """This method adds an object to the manager context.
        :param name: Name of context
        :param obj: Context object
        """
        self.command_sequencer._add_context(name, obj)

    def start_process_monitor(self, process_monitor):
        """This method starts the process monitor thread.
        :param obj: process monitor object
        """
        self.command_sequencer._start_process_monitor(process_monitor)
