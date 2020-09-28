"""Command sequence manager adapter

Adapter which exposes the underlying Command sequence manager module
"""
import logging

from tornado.escape import json_decode
from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTreeError

from odin_sequencer import CommandSequenceError
from .command_sequencer import CommandSequencer


class CommandSequenceManagerAdapter(ApiAdapter):

    def __init__(self, **kwargs):
        """Initialise the CommandSequenceManagerAdapter object.

        This constructor initialises the CommandSequenceManagerAdapter object.
        :param kwargs: keyword arguments specifying options
        """
        # Initialise superclass
        super(CommandSequenceManagerAdapter, self).__init__(**kwargs)
        self.command_sequencer = CommandSequencer()

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
        except ParameterTreeError as e:
            response = {'error': str(e)}
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
        except CommandSequenceError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        logging.debug(response)

        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'CommandSequenceManagerAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)
