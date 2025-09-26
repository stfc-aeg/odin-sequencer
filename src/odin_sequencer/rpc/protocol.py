"""Protocol for odin-sequencer RPC communication.

This module implements the protocol for remote procedure call (RPC) communication with the odin
sequencer. The protocol is based on the JSON-RPC 2.0 specification:

https://www.jsonrpc.org/specification

Tim Nicholls, STFC Detector Systems Software Group
"""

import base64
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, ClassVar, Optional, Union

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

try:
    from enum import IntEnum, StrEnum
except ImportError:  # Python < 3.11
    from enum import Enum, EnumMeta

    class InEnumMeta(EnumMeta):
        """Metaclass for enum classes to add __contains__ method. and allow 'in' operator use."""

        def __contains__(cls, item) -> bool:
            """Check if an item is a valid member of the class."""
            try:
                cls(item)
                return True
            except ValueError:
                return False

    class IntEnum(int, Enum, metaclass=InEnumMeta):
        """Integer enumeration base class for Python versions < 3.11.

        Provides integer enumeration functionality similar to the built-in IntEnum in Python 3.11+.
        """

        pass

    class StrEnum(str, Enum, metaclass=InEnumMeta):
        """String enumeration base class for Python versions < 3.11.

        Provides string enumeration functionality similar to the built-in StrEnum in Python 3.11+.
        """

        def __str__(self) -> str:
            """Return the string representation of the enum member."""
            return self.value


class ValidationError(Exception):
    """Exception raised for validation errors in protocol models."""

    pass


class JsonRpcEncoder(json.JSONEncoder):
    """Custom JSON encoder for JSON-RPC messages.

    Handles serialization of additional types such as numpy arrays.
    """

    def default(self, obj: Any) -> Any:
        """Override the default method to handle additional types.

        Parameters
        ----------
        obj : Any
            The object to serialize.

        Returns
        -------
            A JSON-serializable representation of the object.

        """
        if has_numpy and isinstance(obj, NpArrayType):
            return {
                "type": "ndarray",
                "dtype": str(obj.dtype),
                "shape": list(obj.shape),
                "data": base64.b64encode(obj.tobytes()).decode("utf-8"),
            }
        elif is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


class JsonRpcDecoder(json.JSONDecoder):
    """Custom JSON decoder for JSON-RPC messages.

    Handles deserialization of additional types such as numpy arrays.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the decoder with a custom object hook."""
        super().__init__(*args, object_hook=self.object_hook, **kwargs)

    def object_hook(self, obj: Any) -> Any:
        """Handle additional types during decoding in the custom object hook.

        Parameters
        ----------
        obj : Any
            The JSON object to decode.

        Returns
        -------
            The decoded object, potentially converted to a specific type.

        """
        if (
            isinstance(obj, dict)
            and all(key in obj for key in ("type", "dtype", "shape", "data"))
            and obj["type"] == "ndarray"
        ):
            if has_numpy:
                data = base64.b64decode(obj["data"])
                array = np.frombuffer(data, dtype=obj["dtype"]).reshape(obj["shape"])
                return array
            else:
                raise ValidationError("JSON message contains ndarray but numpy is not available")
        return obj


@dataclass
class JsonRpcModel:
    """Base model for JSON-RPC 2.0 messages.

    Provides common fields and encode/decode methods for JSON-RPC communication.
    """

    JSONRPC_VERSION: ClassVar[str] = "2.0"
    jsonrpc: str = field(default=JSONRPC_VERSION, init=False)
    id: Union[int, str]

    def encode(self) -> bytes:
        """Encode the model to a JSON-formatted UTF-8 byte string."""
        return json.dumps(self.__dict__, cls=JsonRpcEncoder).encode("utf-8")

    @classmethod
    def validate_version(cls, obj: dict):
        """Validate that the provided version matches the JSON-RPC version.

        Parameters
        ----------
        obj : dict
            The JSON-RPC message dictionary to validate.

        Raises
        ------
            ValidationError: If the provided version does not match the expected JSON-RPC version

        """
        if obj.get("jsonrpc", cls.JSONRPC_VERSION) != cls.JSONRPC_VERSION:
            raise ValidationError(f"Invalid jsonrpc version: {obj.get('jsonrpc')}")
        obj.pop("jsonrpc", None)

    @classmethod
    def decode(cls, json_bytes: bytes) -> "JsonRpcModel":
        """Decode a JSON-formatted UTF-8 byte string into a model instance.

        Parameters
        ----------
        json_bytes : bytes
            The JSON-formatted UTF-8 byte string to decode

        Returns
        -------
            An instance of the model decoded from the JSON string

        """
        obj = json.loads(json_bytes.decode("utf-8"), cls=JsonRpcDecoder)
        cls.validate_version(obj)

        return cls(**obj)


class ExecuteScope(StrEnum):
    """Enumeration of execution scopes for RPC execute calls.

    SEQUENCE: Execute a sequence
    CONTEXT: Execute a method exposed by a specific context
    """

    SEQUENCE = "sequence"
    CONTEXT = "context"


@dataclass
class ExecuteParams:
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
    context: str = None
    args: list[Any] | dict[str, Any] = None
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the relationship between the scope and context attributes.

        - Ensure that a valid scope (specified in ExecuteScope) is provided
        - If scope is ExecuteScope.CONTEXT, ensures that context is specified
        - If scope is ExecuteScope.SEQUENCE, ensures that context is not specified

        Raises:
            ValidationError: If the context attribute does not match the requirements for the given
            scope

        """
        if self.scope not in ExecuteScope:
            raise ValidationError(f"Invalid execute scope: {self.scope}")

        match self.scope:
            case ExecuteScope.CONTEXT:
                if not self.context:
                    raise ValidationError("An execute in context scope must specify a context")
            case ExecuteScope.SEQUENCE:
                if self.context is not None:
                    raise ValidationError("An execute in sequence scope must not specify a context")


@dataclass
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
    params: ExecuteParams | list[Any] | dict[str, Any] | None = field(default_factory=list)


@dataclass
class RpcResponse(JsonRpcModel):
    """RPC response message model.

    Represents a JSON-RPC 2.0 response message with a result attribute.

    Attributes
    ----------
    result : Result
        The result of the RPC call, which may be any supported type or None

    """

    result: Result = None  # type: ignore


class RpcErrorCode(IntEnum):
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


@dataclass
class ErrorParams:
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

    def __post_init__(self):
        """Validate that the code attribute is a valid RpcErrorCode.

        Raises:
            ValidationError: If the code attribute is not a valid RpcErrorCode

        """
        if self.code not in RpcErrorCode:
            raise ValidationError(f"Invalid error code: {self.code}")


@dataclass
class RpcErrorResponse(JsonRpcModel):
    """RPC error response message model.

    Represents a JSON-RPC 2.0 error response message with error details.

    Attributes
    ----------
    error : ErrorParams
        The error details including code, message, and optional data

    """

    error: ErrorParams

    def __post_init__(self):
        """Validate that the error attribute is an instance of ErrorParams.

        Raises:
            ValidationError: If the error attribute is not an instance of ErrorParams

        """
        if not isinstance(self.error, ErrorParams):
            try:
                self.error = ErrorParams(**self.error)
            except Exception:
                raise ValidationError("The error attribute must be an instance of ErrorParams")


class RpcResponseAdapter:
    """Adapter for decoding JSON-RPC response or error messages.

    Determines the response type based on the presence of the "error" field and returns the
    appropriate response instance.
    """

    def decode(self, json_bytes: bytes) -> Union[RpcResponse, RpcErrorResponse]:
        """Decode a JSON-formatted UTF-8 byte string into a response or error model instance.

        Parameters
        ----------
        json_bytes : bytes
            The JSON-formatted UTF-8 byte string to decode

        Returns
        -------
        RpcResponse | RpcErrorResponse
            An instance of the response or error model decoded from the JSON string

        """
        response = json.loads(json_bytes.decode("utf-8"), cls=JsonRpcDecoder)
        JsonRpcModel.validate_version(response)

        if "error" in response:
            return RpcErrorResponse(**response)
        else:
            return RpcResponse(**response)
