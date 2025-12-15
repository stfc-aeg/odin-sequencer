"""Utility functions for the sequencer RPC server.

This module provides various utility functions.

Tim Nicholls, STFC Detector Systems Software Group.
"""

from functools import wraps
from threading import Thread

from .protocol import ErrorParams, RpcErrorResponse, RpcResponse


def dispatched_method(in_thread=False):
    """Decorate a method for use in the RPC server dispatch table.

    This decorator enables methods to be used in the RPC server dispatch table, allowing them to
    be run directly or in a separate thread as necessary.

    :param in_thread: run method in thread (default is False)
    """

    def _decorator(method):
        @wraps(method)
        def _impl(_self, client_id, request_id, *args, **kwargs):
            def _call_method():
                """Call the method and return an appropriate response."""
                try:
                    result = method(_self, *args, **kwargs)
                    return RpcResponse(id=request_id, result=result)
                except Exception as e:
                    return RpcErrorResponse(
                        id=request_id,
                        error=ErrorParams(
                            code=-32603,
                            message=f"Error calling method {method.__name__} "
                            f"for client id {client_id.decode('utf-8')}",
                            data=str(e),
                        ),
                    )

            def _target():
                """Execute function and send back response when run in thread."""
                response = _call_method()
                _self.send_result(client_id, response)

            # If the decorated method should run in a thread, create and start one. Otherwise call
            # the method directly.
            if in_thread:
                t = Thread(target=_target)
                t.start()
                response = None
            else:
                response = _call_method()
            return response

        return _impl

    return _decorator
