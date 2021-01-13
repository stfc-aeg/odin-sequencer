"""Demo adapter for ODIN sequencer 

This class implements a simple adapter used for demonstrating how a context can be
added to the odin sequencer.

Rhys Evans, STFC
"""
import logging

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types


class DummyContextAdapter(ApiAdapter):
    """Dummy context adapter class for the ODIN server.

    This adapter provides a TestDevice context to the odin sequencer.
    """

    def __init__(self, **kwargs):
        """Initialize the DummyContextAdapter object.

        This constructor initializes the DummyContextAdapter object.

        :param kwargs: keyword arguments specifying options
        """
        # Intialise superclass
        super(DummyContextAdapter, self).__init__(**kwargs)

        self.adapters = {}

        logging.debug('DummyContextAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response[path] = self.adapters['odin_sequencer'].get(path, request).data
            status_code = 200
        except Exception as e:
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
        content_type = 'application/json'
        try:
            body = decode_request_body(request)
            response = {}
            request = ApiAdapterRequest(body)
            response[path] = self.adapters['odin_sequencer'].put(path, request).data
            status_code = 200
        except DummyContextError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def initialize(self, adapters):
        """Initialize the adapter after it has been loaded and added TestDevice context to sequencer.

        Receive a dictionary of all loaded adapters so that they may be accessed by this adapter.
        Remove itself from the dictionary so that it does not reference itself, as doing so
        could end with an endless recursive loop.
        """

        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        logging.debug("Received following dict of Adapters: %s", self.adapters)
        
        test_device = TestDevice(123)
        self.adapters['odin_sequencer'].add_context('test_device', test_device)
        logging.debug("Test device context added to odin sequencer.")


class DummyContextError(Exception):
    """Simple exception class to wrap lower-level exceptions."""

    pass


class TestDevice():

    def __init__(self, val):
        self.val = val

    def read_reg(self):
        print("In read reg")
        return self.val

    def write_reg(self, reg, vals):
        print("In write reg with reg {} vals {}".format(reg, vals))
