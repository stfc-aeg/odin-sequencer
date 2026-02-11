"""server.py - RPC server implementation for odin-sequencer.

This module implements an RPC server for odin-sequencer. Ths server provides ZeroMQ communication
channels for clients to make RPC call using JSON-RPC, handles incoming RPC requests, dipatching
them to appropriate handlers for interaction with the sequencer. This incldues execution of loaded
sequences and method calls to contexts.

Tim Nicholls, STFC Detector Systems Software Group.
"""

import logging
import time

import zmq
from zmq.error import ZMQError
from zmq.eventloop.zmqstream import ZMQStream

from .protocol import (
    ErrorParams,
    ExecuteParams,
    ExecuteScope,
    RpcErrorCode,
    RpcErrorResponse,
    RpcRequest,
    RpcResponse,
    ValidationError,
)
from .util import dispatched_method


class RpcServerError(Exception):
    """Exception raised for errors encountered in the RPC server.

    Attributes:
        code: Error code associated with the exception.
        message: Description of the error.
        data: Additional data related to the error.

    """

    def __init__(self, code, message, data):
        """Initialize RpcServerError with error code, message, and additional data.

        Args:
            code: Error code associated with the exception.
            message: Description of the error.
            data: Additional data related to the error.

        """
        super().__init__(f"{message}: {data}")
        self.code = code
        self.message = message
        self.data = data


class RpcServer:
    """RPC server for odin-sequencer.

    Handles incoming RPC requests, dispatches them to registered handlers,
    manages ZeroMQ communication channels, and provides logging and error handling.
    """

    def __init__(self, sequencer, manager, options={}):
        """Initialize the RPC server with sequencer, manager, and options.

        Args:
            sequencer: The sequencer instance.
            manager: The manager instance.
            options: Optional dictionary of configuration parameters.

        """
        self.sequencer = sequencer
        self.manager = manager

        rpc_addr = options.get("rpc_addr", "127.0.0.1")
        ctrl_port = options.get("rpc_ctrl_port", 5555)
        log_port = options.get("rpc_log_port", 6666)
        self.ctrl_endpoint = f"tcp://{rpc_addr}:{ctrl_port}"
        self.log_endpoint = f"tcp://{rpc_addr}:{log_port}"

        try:
            self.ctx = zmq.Context()

            self.ctrl_channel = self.ctx.socket(zmq.ROUTER)
            self.ctrl_channel.bind(self.ctrl_endpoint)
            self.ctrl_stream = ZMQStream(self.ctrl_channel)
            self.ctrl_stream.on_recv(self.handle_receive)
            logging.debug(
                "Sequencer RPC server control endpoint initialised on %s", self.ctrl_endpoint
            )

            self.log_channel = self.ctx.socket(zmq.PUB)
            self.log_channel.bind(self.log_endpoint)
            logging.debug("Sequencer RPC server log endpoint initialised on %s", self.log_endpoint)

            self.result_endpoint = "inproc://result"
            self.result_rx_channel = self.ctx.socket(zmq.PULL)
            self.result_rx_channel.bind(self.result_endpoint)
            self.result_rx_stream = ZMQStream(self.result_rx_channel)
            self.result_rx_stream.on_recv(self.handle_result)

            self.result_tx_channel = self.ctx.socket(zmq.PUSH)
            self.result_tx_channel.connect(self.result_endpoint)

        except ZMQError as error:
            logging.error("Error initializing RPC server: %s", error)

        self.dispatcher = {
            "ping": self.ping,
            "get_contexts": self.get_contexts,
            "execute": self.execute,
            "abort": self.abort,
            "reload": self.reload,
        }

        self.manager.register_logger(self.logger)

    def handle_receive(self, msg):
        """Handle incoming messages from the control channel.

        Args:
            msg: The received message as a list of bytes.

        """
        client_id = msg[0]
        response = None

        try:
            request = RpcRequest.decode(msg[1])
            response = self.dispatch_request(client_id, request)

        except ValidationError as error:
            response = RpcErrorResponse(
                id=None,
                error=ErrorParams(
                    code=RpcErrorCode.InvalidRequest, message="Invalid request", data=str(error)
                ),
            )

        if response:
            if isinstance(response, RpcErrorResponse):
                logging.error("%s : %s", response.error.message, response.error.data)

            self.ctrl_channel.send_multipart([client_id, response.encode()])

    def dispatch_request(self, client_id: bytes, request: RpcRequest):
        """Dispatch an RPC request to the appropriate handler.

        Args:
            client_id: The client identifier.
            request: The decoded RpcRequest object.

        Returns:
            The response object to be sent back to the client.

        """
        response = None

        if request.method in self.dispatcher:
            try:
                if isinstance(request.params, dict):
                    response = self.dispatcher[request.method](
                        client_id, request.id, **request.params
                    )
                else:
                    response = self.dispatcher[request.method](
                        client_id, request.id, *request.params
                    )
            except RpcServerError as e:
                response = RpcErrorResponse(
                    id=request.id, code=e.code, message=e.message, data=e.data
                )
            except Exception as e:
                response = RpcResponse(
                    id=request.id,
                    error=ErrorParams(
                        code=RpcErrorCode.InternalError, message="Internal error", data=str(e)
                    ),
                )
        else:
            # Method not found
            response = RpcErrorResponse(
                id=request.id,
                error=ErrorParams(
                    code=RpcErrorCode.MethodNotFound,
                    message="Method not found",
                    data=request.method,
                ),
            )

        return response

    def send_result(self, client_id, response):
        """Send the result of an RPC call to the client.

        Args:
            client_id: The client identifier.
            response: The response object to send.

        """
        if isinstance(response, RpcErrorResponse):
            logging.error("%s : %s", response.error.message, response.error.data)

        self.result_tx_channel.send_multipart([client_id, response.encode()])

    def handle_result(self, msg):
        """Handle result messages and forward them to the control channel.

        Args:
            msg: The result message as a list of bytes.

        """
        self.ctrl_channel.send_multipart(msg)

    def logger(self, message, level):
        """Log messages to the log channel.

        Args:
            *args: Message components.
            **kwargs: Additional keyword arguments.

        """
        if level:
            message = f"{level.upper()}: {message}"
        self.log_channel.send_string(message)

    @dispatched_method()
    def ping(self):
        """Ping the RPC server to check connectivity.

        Returns:
            True if the server is reachable.

        """
        logging.debug("Ping received")
        return True

    @dispatched_method()
    def get_contexts(self):
        """Get available contexts from the sequencer.

        Returns:
            A list of context names.

        """
        contexts = list(self.manager.context.keys())
        logging.debug("Getting contexts: %s", contexts)
        return contexts

    @dispatched_method(in_thread=True)
    def execute(self, **params):
        """Execute a method in the specified scope.

        Args:
            **params: Parameters for execution.

        Returns:
            The result of the executed method.

        Raises:
            RpcServerError: If the scope is invalid.

        """
        msg = ExecuteParams(**params)

        match msg.scope:
            case ExecuteScope.SEQUENCE:
                # Execute in sequence scope
                result = self.manager.execute(msg.method, *msg.args, **msg.kwargs)
            case ExecuteScope.CONTEXT:
                # Execute in context scope
                ctx = self.manager._get_context(msg.context)
                result = getattr(ctx, msg.method)(*msg.args, **msg.kwargs)
            case _:
                raise RpcServerError(
                    code=RpcErrorCode.InvalidScope, message="Invalid scope", data=msg.scope
                )

        return result

    @dispatched_method(in_thread=True)
    def abort(self):
        """Abort the currently running sequence.

        Returns:
            True if the sequence was aborted.

        Raises:
            RpcServerError: If no sequence is executing.

        """
        if not self.manager.is_executing:
            raise RpcServerError(
                code=RpcErrorCode.AbortError, message="Abort error", data="no sequence is executing"
            )

        self.manager.abort_sequence = True

        while self.manager.is_executing:
            time.sleep(0.1)

        logging.debug("Execution of running sequence aborted")
        self.manager.abort_sequence = False

        return True

    @dispatched_method()
    def reload(self):
        """Reload the sequences in the sequencer.

        Returns:
            True if reload was successful.

        """
        logging.debug("Reload sequences")
        self.sequencer.set_reload(True)

        return not self.sequencer.module_reload_failed
