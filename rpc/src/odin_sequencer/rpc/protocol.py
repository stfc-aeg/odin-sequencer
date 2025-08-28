"""Protocol for odin-sequencer RPC communication.

This module implements the protocol for remote procedure call (RPC) communication with the odin
sequencer. The protocol is based on the JSON-RPC 2.0 specification:

https://www.jsonrpc.org/specification

Tim Nicholls, STFC Detector Systems Software Group
"""

import base64
import enum
from typing import Annotated, Any, Literal, Optional, Self, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Discriminator,
    Tag,
    TypeAdapter,
    ValidationError,  # noqa: F401
    field_serializer,
    field_validator,
    model_validator,
)

# If numpy is available, add the ndarray type to the result types
result_types = [Any]
try:
    import numpy as np

    NpArrayType = np.ndarray
    has_numpy = True
    result_types.append(NpArrayType)
except ImportError:
    NpArrayType = None
    has_numpy = False

Result = Optional[Union[tuple(result_types)]]


class JsonRpcModel(BaseModel):
    """Base model for JSON-RPC 2.0 messages.

    Provides common fields and encode/decode methods for JSON-RPC communication.
    """

    jsonrpc: Literal["2.0"] = "2.0"
    id: int | str | None

    def encode(self) -> bytes:
        """Encode the model to a JSON-formatted UTF-8 byte string."""
        return self.model_dump_json(round_trip=True).encode("utf-8")

    @classmethod
    def decode(cls, json: bytes):
        """Decode a JSON-formatted UTF-8 byte string into a model instance.

        Parameters
        ----------
        json : bytes
            The JSON-formatted UTF-8 byte string to decode

        Returns
        -------
            An instance of the model decoded from the JSON string

        """
        return cls.model_validate_json(json.decode("utf-8"))


class ExecuteScope(enum.StrEnum):
    """Enumeration of execution scopes for RPC execute calls.

    SEQUENCE: Execute a sequence
    CONTEXT: Execute a method exposed by a specific context
    """

    SEQUENCE = "sequence"
    CONTEXT = "context"


class ExecuteParams(BaseModel):
    """Parameters for an RPC execute call.

    Attributes
    ----------
    scope : ExecuteScope
        The scope of execution, either 'sequence' or 'context'
    method : str
        The method to execute
    context : str | None
        The context in which to execute the method (required for context scope)
    args : list[Any] | dict[str, Any] | None
        Positional or keyword arguments for the method
    kwargs : dict[str, Any] | None
        Additional keyword arguments for the method

    """

    scope: ExecuteScope
    method: str
    context: str | None = None
    args: list[Any] | dict[str, Any] | None = None
    kwargs: dict[str, Any] | None = {}

    @model_validator(mode="after")
    def check_scope_context(self) -> Self:
        """Validate the relationship between the scope and context attributes.

        - If scope is ExecuteScope.CONTEXT, ensures that context is specified
        - If scope is ExecuteScope.SEQUENCE, ensures that context is not specified

        Raises:
            ValueError: If the context attribute does not match the requirements for the given scope

        Returns:
            Self: Returns the instance for method chaining

        """
        match self.scope:
            case ExecuteScope.CONTEXT:
                if self.context is None:
                    raise ValueError("An execute in context scope must specify a context")
            case ExecuteScope.SEQUENCE:
                if self.context is not None:
                    raise ValueError("An execute in sequence scope must not specify a context")
        return self


class RpcRequest(JsonRpcModel):
    """RPC request message model.

    Represents a JSON-RPC 2.0 request message with method and parameters.

    Attributes
    ----------
    method : str
        The name of the method to invoke.
    params : ExecuteParams | list[Any] | dict[str, Any] | None
        The parameters to pass to the method.

    """

    method: str
    params: ExecuteParams | list[Any] | dict[str, Any] | None = []


class RpcResponse(JsonRpcModel):
    """RPC response message model.

    Represents a JSON-RPC 2.0 response message with a result attribute.

    Attributes
    ----------
    result : Result
        The result of the RPC call, which may be any supported type or None

    """

    result: Result = None  # type: ignore

    @field_serializer("result")
    def serialize_result(self, value: Any) -> Result:  # type: ignore
        """Serialize the result field for JSON encoding.

        Parameters
        ----------
        value : Any
            The value to serialize, which may be a numpy ndarray or any other type

        Returns
        -------
        Any
            The serialized value, either as a dictionary for ndarrays or the original value

        """

        def _recursive_serialize(value: Any) -> Any:
            if isinstance(value, list):
                return [_recursive_serialize(v) for v in value]
            elif isinstance(value, tuple):
                return tuple([_recursive_serialize(v) for v in value])
            elif isinstance(value, dict):
                return {k: _recursive_serialize(v) for k, v in value.items()}
            elif has_numpy and isinstance(value, NpArrayType):
                return {
                    "type": "ndarray",
                    "dtype": str(value.dtype),
                    "shape": list(value.shape),
                    "data": base64.b64encode(value.tobytes()).decode("utf-8"),
                }
            else:
                return value

        return _recursive_serialize(value)

    @field_validator("result", mode="before")
    def validate_result(cls, value):
        """Validate and decode the result field, handling special types like numpy ndarrays.

        Parameters
        ----------
        value : Any
            The value to validate and decode

        Returns
        -------
        Any
            The decoded value, possibly a numpy ndarray

        Raises
        ------
        ImportError
            If the result type is ndarray but numpy is not installed
        TypeError
            If an unknown type tag is encountered

        """

        def _recursive_validate(value: Any) -> Any:
            if isinstance(value, list):
                return [_recursive_validate(v) for v in value]
            elif isinstance(value, tuple):
                return tuple([_recursive_validate(v) for v in value])
            elif isinstance(value, dict):
                if (
                    all(k in value for k in ["type", "data", "dtype", "shape"])
                    and value["type"] == "ndarray"
                ):
                    if has_numpy:
                        data = base64.b64decode(value["data"])
                        array = np.frombuffer(data, dtype=value["dtype"])
                        return array.reshape(value["shape"])
                    else:
                        raise ImportError("Result contains ndarray but numpy is not installed")
                else:
                    return {k: _recursive_validate(v) for k, v in value.items()}
            else:
                return value

        return _recursive_validate(value)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RpcErrorCode(enum.IntEnum):
    """Enumeration of standard and implementation-defined error codes for JSON-RPC responses.

    ParseError : Invalid JSON was received
    InvalidRequest : The JSON sent is not a valid request object
    MethodNotFound : The method does not exist or is unavailable
    InvalidParams : Invalid method parameter(s)
    InternalError : Internal JSON-RPC error
    InvalidScope : Invalid execution scope for the request
    AbortError : The request was aborted by the server
    """

    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    InvalidScope = -32000
    # Error codes -32000 to -32099 are reserved for implementation-defined server errors
    AbortError = -32001


class ErrorParams(BaseModel):
    """Parameters for an RPC error response.

    Attributes
    ----------
    code : RpcErrorCode
        The error code indicating the type of error.
    message : str
        A descriptive error message.
    data : Optional[Any]
        Additional data about the error, if available.

    """

    code: RpcErrorCode
    message: str
    data: Optional[Any] = None


class RpcErrorResponse(JsonRpcModel):
    """RPC error response message model.

    Represents a JSON-RPC 2.0 error response message with error details.

    Attributes
    ----------
    error : ErrorParams
        The error details including code, message, and optional data

    """

    error: ErrorParams


class RpcResponseAdapter(TypeAdapter):
    """Adapter for decoding JSON-RPC response or error messages.

    Determines the response type (success or error) and validates the JSON accordingly.
    """

    @staticmethod
    def _get_resp_type(response: dict) -> str:
        return "error" if "error" in response else "response"

    def __init__(self):
        """Initialize the RpcResponseAdapter with response and error type discrimination."""
        super().__init__(
            Annotated[
                Union[
                    Annotated[RpcResponse, Tag("response")],
                    Annotated[RpcErrorResponse, Tag("error")],
                ],
                Discriminator(RpcResponseAdapter._get_resp_type),
            ]
        )

    def decode(self, json: bytes) -> Union[RpcResponse, RpcErrorResponse]:
        """Decode a JSON-formatted UTF-8 byte string into a response or error model instance.

        Parameters
        ----------
        json : bytes
            The JSON-formatted UTF-8 byte string to decode

        Returns
        -------
        RpcResponse | RpcErrorResponse
            An instance of the response or error model decoded from the JSON string

        """
        return self.validate_json(json)
