"""client.py - RPC client implementation for odin-sequencer.

This module provides the OdinSequencerClient class for interacting with the odin-sequencer RPC
server. It allows sending requests, receiving responses, and managing contexts for remote procedure
calls.

Tim Nicholls, STFC Detector Systems Software Group.
"""

import random
from typing import Any, List

import zmq

from .protocol import ExecuteParams, ExecuteScope, RpcErrorResponse, RpcRequest, RpcResponseAdapter


class OdinSequencerClientError(Exception):
    """Exception raised for errors encountered in the OdinSequencerClient.

    Used to signal errors returned from the RPC server or client-side failures.
    """

    pass


class OdinSequencerClient:
    """Client for interacting with odin-sequencer via remote procedure calls (RPC).

    This class manages ZeroMQ connections to the sequencer server, sends requests,
    receives responses, and provides methods for sequence and context operations.
    """

    def __init__(
        self, seq_address: str, ctrl_port: int = 5555, log_port: int = 6666, emit_exceptions=True
    ):
        """Initialize the OdinSequencerClient.

        Args:
            seq_address: Address of the sequencer server.
            ctrl_port: Control port for RPC requests.
            log_port: Log port for receiving log messages.
            emit_exceptions: Whether to raise exceptions on RPC errors.

        """
        self.ctrl_endpoint = f"tcp://{seq_address}:{ctrl_port}"
        self.log_endpoint = f"tcp://{seq_address}:{log_port}"
        self.emit_exceptions = emit_exceptions

        self.ctx = zmq.Context()

        self.ctrl_socket = self.ctx.socket(zmq.DEALER)
        identity = "{:04x}-{:04x}".format(random.randrange(0x10000), random.randrange(0x10000))
        self.ctrl_socket.setsockopt(zmq.IDENTITY, identity.encode("utf-8"))
        self.ctrl_socket.connect(self.ctrl_endpoint)

        self.log_socket = self.ctx.socket(zmq.SUB)
        self.log_socket.connect(self.log_endpoint)
        self.log_socket.subscribe("")

        self.poller = zmq.Poller()
        self.poller.register(self.ctrl_socket, zmq.POLLIN)
        self.poller.register(self.log_socket, zmq.POLLIN)

        self.request_id = 0
        self.response_adapter = RpcResponseAdapter()

    def close(self):
        """Close all sockets and terminate the ZeroMQ context."""
        self.ctrl_socket.close()
        self.log_socket.close()
        self.ctx.term()

    def _next_id(self) -> int:
        """Generate a new unique request ID for RPC calls.

        Returns:
            int: The next request ID.

        """
        self.request_id += 1
        return self.request_id

    def do_request(self, request: RpcRequest) -> Any:
        """Send an RPC request and wait for the response.

        Args:
            request: The RpcRequest object to send.

        Returns:
            The result from the RPC response if available
        Raises:
            OdinSequencerClientError: If an error response is received and emit_exceptions is True

        """
        self.ctrl_socket.send(request.encode())

        response = self.await_response()

        if isinstance(response, RpcErrorResponse):
            error_msg = f"{response.error.message} : {response.error.data}"
            if self.emit_exceptions:
                raise OdinSequencerClientError(error_msg)
            else:
                print(error_msg)
                return None

        return response.result

    def await_response(self) -> Any:
        """Wait for and return the next response from the RPC server.

        Polls both the control and log sockets, handling log messages and returning
        the decoded response from the control socket when available.

        Returns:
            Any: The decoded response from the RPC server.

        """
        response = None

        while response is None:
            socks = dict(self.poller.poll(1000))
            if self.ctrl_socket in socks and socks[self.ctrl_socket] == zmq.POLLIN:
                reply = self.ctrl_socket.recv()
                response = self.response_adapter.decode(reply)
            if self.log_socket in socks and socks[self.log_socket] == zmq.POLLIN:
                msg = self.log_socket.recv_multipart()
                self.handle_log_message(msg)

        return response

    def handle_log_message(self, msg: List[bytes]):
        """Handle a log message received from the sequencer server.

        Args:
            msg: List of bytes representing the log message.

        """
        print(" ".join((x.decode("utf-8") for x in msg)))

    def execute(self, method: str, *args, **kwargs):
        """Execute a sequence in the sequencer.

        Args:
            method: The method name to execute.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.

        Returns:
            The result of the executed method.

        """
        result = None

        req = RpcRequest(
            method="execute",
            params=ExecuteParams(
                scope=ExecuteScope.SEQUENCE, method=method, args=args, kwargs=kwargs
            ),
            id=self._next_id(),
        )
        try:
            result = self.do_request(req)
        except KeyboardInterrupt:
            print("Keyboard interrupt received, aborting execution")
            self.abort()
        return result

    def get_contexts(self) -> List[str]:
        """Retrieve the list of available context names from the sequencer.

        Returns:
            List of context names.

        """
        req = RpcRequest(method="get_contexts", id=self._next_id())
        return self.do_request(req)

    def get_context(self, name: str) -> "Context":
        """Get a Context object for the specified context name.

        Args:
            name: The name of the context.

        Returns:
            Context: The context object for remote method calls.

        """
        return Context(self, name)

    def abort(self):
        """Abort the currently running sequence on the sequencer.

        Returns:
            Result of the abort operation.

        """
        abort_request = RpcRequest(method="abort", id=self._next_id())
        result = self.do_request(abort_request)
        # Flush response to abort command
        self.await_response()
        return result

    def reload(self):
        """Reload the sequences on the sequencer.

        Returns:
            Result of the reload operation.

        """
        reload_request = RpcRequest(method="reload", id=self._next_id())
        return self.do_request(reload_request)


class Context:
    """Represents a remote context in the odin-sequencer server.

    Allows dynamic method calls on the context using attribute access.
    """

    def __init__(self, sequencer: OdinSequencerClient, name: str):
        """Initialize the Context object.

        Args:
            sequencer: The OdinSequencerClient instance.
            name: The name of the context.

        Raises:
            ValueError: If the context name is not found in the sequencer.

        """
        self.sequencer = sequencer
        self.name = name

        if self.name not in self.sequencer.get_contexts():
            raise ValueError(f"Context '{self.name}' not found in sequencer.")

    def execute(self, method: str, *args, **kwargs):
        """Execute a method on this context via RPC.

        Args:
            method: The method name to execute.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.

        Returns:
            The result of the executed method.

        """
        req = RpcRequest(
            method="execute",
            params=ExecuteParams(
                scope=ExecuteScope.CONTEXT,
                context=self.name,
                method=method,
                args=args,
                kwargs=kwargs,
            ),
            id=self.sequencer._next_id(),
        )
        return self.sequencer.do_request(req)

    def __getattr__(self, name: str):
        """Dynamically handle method calls on the context.

        Args:
            name: The method name to call.

        Returns:
            Callable that executes the method via RPC.

        """

        def wrapper(*args, **kwargs):
            return self.execute(name, *args, **kwargs)

        return wrapper
