"""Command sequence manager adapter

Adapter which exposes the underlying Command sequence manager module

Viktor Bozhinov, STFC.
"""
from odin_control.adapters.adapter import ApiAdapter, ApiAdapterResponse, response_types

from odin_sequencer import SequencerError
from .controller import SequencerController


class SequencerAdapter(ApiAdapter):
    """ ApiAdapter for the Command Sequencer.

    Adapter which exposes the underlying Command Sequencer.
    """
    controller_cls = SequencerController
    error_cls = SequencerError

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object

        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            # Decode query parameters
            query_params = {k: [val.decode("utf-8") for val in v] for (k, v) in request.query_arguments.items()}
            response = self.controller.get(path, kwargs=query_params)
            status_code = 200
        except SequencerError as error:
            response = {'error': str(error)}
            status_code = 400

        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def add_context(self, name, obj):
        """This method adds an object to the manager context.
        :param name: Name of context
        :param obj: Context object
        """
        self.controller._add_context(name, obj)

    def start_process_monitor(self, process_monitor):
        """This method starts the process monitor thread.
        :param obj: process monitor object
        """
        self.controller._start_process_monitor(process_monitor)
