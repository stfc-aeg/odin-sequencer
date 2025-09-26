"""Tests for the odin sequencer RPC protocol.

Tim Nicholls, STFC Detector Systems Software Group
"""

import base64
import pytest
import numpy as np
from odin_sequencer.rpc.protocol import (
    ErrorParams,
    ExecuteParams,
    ExecuteScope,
    JsonRpcModel,
    RpcErrorCode,
    RpcErrorResponse,
    RpcRequest,
    RpcResponse,
    RpcResponseAdapter,
    ValidationError,
)


class TestJsonRpcModel:
    """Test cases for the JsonRpcModel class (which underlies the RPC protocol)."""

    def test_model_fields(self):
        """Test that the model has jsonrpc verions and id fields."""
        model = JsonRpcModel(id=1)

        assert model.jsonrpc == "2.0"
        assert model.id == 1

    def test_model_version_const(self):
        """Test that attempting to create a model with a different version raises an exception."""
        with pytest.raises(TypeError):
            _ = JsonRpcModel(jsonrpc="1.0", id=1)

    def test_model_str_id(self):
        """Test that the model also accepts string id fields."""
        model = JsonRpcModel(id="one")

        assert model.id == "one"

    def test_model_no_id(self):
        """Test that the model also accepts an empty (null) id field."""
        model = JsonRpcModel(id=None)

        assert model.id is None

    def test_model_encodes_to_bytes(self):
        """Test that the model implements an encode method which encodes to bytes."""
        model = JsonRpcModel(id=1)
        encoded = model.encode()
        assert isinstance(encoded, bytes)

    def test_model_decodes_from_bytes(self):
        """Test that the model implements a decode method which decodes from bytes."""
        encoded = b'{"id":1}'
        model = JsonRpcModel.decode(encoded)

        assert isinstance(model, JsonRpcModel)
        assert model.jsonrpc == "2.0"
        assert model.id == 1

    def test_model_decode_bad_version(self):
        """Test that decoding a model with an invalid jsonrpc version raises an exception."""
        encoded = b'{"jsonrpc":"1.0","id":1}'

        with pytest.raises(ValidationError):
            _ = JsonRpcModel.decode(encoded)

    def test_model_decode_good_version(self):
        """Test that decoding a model with a valid jsonrpc version works."""
        encoded = b'{"jsonrpc":"2.0","id":1}'
        model = JsonRpcModel.decode(encoded)

        assert isinstance(model, JsonRpcModel)
        assert model.jsonrpc == "2.0"
        assert model.id == 1


class TestExecuteParams:
    """Test cases for the ExecuteParams parameter class."""

    def test_rpc_context_execute(self):
        """Test that a context ExecuteParams object is correctly initialised."""
        scope = ExecuteScope.CONTEXT
        method = "do_it"
        context = "test"
        args = [1, 2, 3]
        kwargs = {"one": 1, "two": 2.0}

        execute = ExecuteParams(
            scope=scope, method=method, context=context, args=args, kwargs=kwargs
        )

        assert execute.scope == scope
        assert execute.method == method
        assert execute.context == context
        assert execute.args == args
        assert execute.kwargs == kwargs

    def test_rpc_sequence_execute(self):
        """Test that a sequence ExecuteParams object is correctly initialised."""
        scope = ExecuteScope.SEQUENCE
        method = "do_it"
        args = [1, 2, 3]
        kwargs = {"one": 1, "two": 2.0}

        execute = ExecuteParams(scope=scope, method=method, args=args, kwargs=kwargs)

        assert execute.scope == scope
        assert execute.method == method
        assert execute.context is None
        assert execute.args == args
        assert execute.kwargs == kwargs

    def test_rpc_context_execute_no_context(self):
        """Test that a context ExecuteParams object must have a context specified."""
        scope = ExecuteScope.CONTEXT
        method = "do_it"

        with pytest.raises(ValidationError):
            _ = ExecuteParams(scope=scope, method=method)

    def test_rpc_sequence_execute_with_context(self):
        """Test that a context ExecuteParams object must not have a context specified."""
        scope = ExecuteScope.SEQUENCE
        method = "do_it"
        context = "test"

        with pytest.raises(ValidationError):
            _ = ExecuteParams(scope=scope, method=method, context=context)

    def test_rpc_execute_no_scope(self):
        """Test thatat an ExecuteParams object cannot be initialsied without a scope."""
        method = "do_it"
        context = "test"
        with pytest.raises(TypeError):
            _ = ExecuteParams(method=method, context=context)

    def test_rpc_excute_bad_scope(self):
        """Test that an ExecuteParams object cannot be initialsied with an unknown scope."""
        scope = "unknown"
        method = "do_it"
        context = "test"

        with pytest.raises(ValidationError):
            _ = ExecuteParams(scope=scope, method=method, context=context)

    def test_rpc_excute_no_method(self):
        """Test that an ExecuteParams object cannot be initialsied without a method."""
        scope = ExecuteScope.CONTEXT
        context = "test"
        with pytest.raises(TypeError):
            _ = ExecuteParams(scope=scope, context=context)


class TestRpcRequest:
    """Test cases for the RpcRequest class."""

    def test_request_correct_init(self):
        """Test that an RpcRequest has the correct field and values."""
        id = 1
        method = "test"
        params = [1, 2, 3]
        request = RpcRequest(id=id, method=method, params=params)

        assert request.jsonrpc == "2.0"
        assert request.id == id
        assert request.method == method
        assert request.params == params

    def test_request_no_params(self):
        """Test that an RpcRequest can be initialised with an empty parameter list."""
        request = RpcRequest(id=1, method="test")

        assert request.params == []

    def test_request_dict_params(self):
        """Test that an RpcRequest can also accept a parameter dict."""
        dict_params = {"one": 1, "two": 2.0, "three": "three"}
        request = RpcRequest(id=1, method="test", params=dict_params)

        assert request.params == dict_params

    def test_request_encodes_to_bytes(self):
        """Test that an RpcRequest correctly encodes to bytes."""
        request = RpcRequest(id=1, method="test", params=[1, 2, 3])
        encoded = request.encode()
        assert isinstance(encoded, bytes)

    def test_request_decodes_from_bytes(self):
        """Test that an RpcRequest correctly decodes from bytes."""
        encoded = b'{"id":1,"method":"test","params":[1,2,3]}'
        request = RpcRequest.decode(encoded)

        assert isinstance(request, RpcRequest)
        assert request.id == 1
        assert request.method == "test"
        assert request.params == [1, 2, 3]

    def test_execute_request(self):
        """Test that an execute request has fields and parameters correctly set."""
        scope = ExecuteScope.CONTEXT
        method = "do_it"
        context = "test"
        args = [1, 2, 3]
        kwargs = {"one": 1, "two": 2.0}
        execute = ExecuteParams(
            scope=scope, method=method, context=context, args=args, kwargs=kwargs
        )

        request = RpcRequest(id=1, method="execute", params=execute)

        assert isinstance(request.params, ExecuteParams)
        assert request.params.scope == scope
        assert request.params.method == method
        assert request.params.context == context
        assert request.params.args == args
        assert request.params.kwargs == kwargs


class TestRpcResponse:
    """Test cases for the RpcResponse class."""

    def test_response_correct_init(self):
        """Test that a basic RpcResponse has the correct fields."""
        id = 2
        result = [123, 456]
        response = RpcResponse(id=id, result=result)

        assert response.id == id
        assert response.result == result
        assert not hasattr(response, "error")

    def test_response_null_result(self):
        """Test that the RpcResponse object will accept an empty result field."""
        id = 2
        result = None
        response = RpcResponse(id=id, result=result)

        assert response.id == id
        assert response.result == result


class TestErrorParams:
    """Test cases for the ErrorParams class."""

    def error_params_correct_init(self):
        """Test that an ErrorParams object has correctly initialised fields."""
        code = RpcErrorCode.ParseError
        message = "parse error"
        data = "there was an error parsing the request"

        error = ErrorParams(code=code, message=message, data=data)

        assert error.code == code
        assert error.message == message
        assert error.data == data

    def test_error_params_illegal_code(self):
        """Test that an ErrorParams object will not accept an illegal error code."""
        with pytest.raises(ValidationError):
            _ = ErrorParams(code=1234, message="parse error", data="data")


class TestRpcErrorResponse:
    """Test cases for the RpcErrorResponse class."""

    def test_error_response_correct_init(self):
        """Test that an RpcErrorResponse object has the correct fields."""
        id = 2
        code = RpcErrorCode.ParseError
        message = "parse error"
        data = "there was an error parsing the request"
        error = ErrorParams(code=code, message=message, data=data)
        response = RpcErrorResponse(id=id, error=error)

        assert response.id == id
        assert isinstance(response.error, ErrorParams)
        assert response.error.code == code
        assert response.error.message == message
        assert response.error.data == data
        assert not hasattr(response, "result")

    def test_error_response_bad_error(self):
        """Test that the RpcErrorResponse object will accept an empty result field."""
        with pytest.raises(ValidationError):
            _ = RpcErrorResponse(id=1, error=123)


class TestRpcResponseAdapter:
    """Test cases for the RpcResponseAdapter."""

    def test_response_adapter_decodes_rpc_response(self):
        """Test that the adapter correctly decodes to an RpcResponse object."""
        response_adapter = RpcResponseAdapter()
        response_bytes = b'{"jsonrpc":"2.0","id":4,"result":[1,2,3,4]}'

        response = response_adapter.decode(response_bytes)

        assert isinstance(response, RpcResponse)

    def test_response_adapter_decodes_rpc_error_response(self):
        """Test that the adapter correctly decodes to an RpcErrorResponse object."""
        response_adapter = RpcResponseAdapter()
        error_bytes = (
            '{"jsonrpc":"2.0","id":4,"error":{"code":-32603,'
            '"message":"internal error","data":"an internal error occurred"}}'.encode("utf-8")
        )

        response = response_adapter.decode(error_bytes)

        assert isinstance(response, RpcErrorResponse)


class TestRpcResponseNumpyResult:
    """Test cases for the RpcResponse class with a numpy array result."""

    def test_response_numpy_array_result(self):
        """Test that an RpcResponse can be correctly initialised with a numpy array result."""
        id = 2
        result = np.array([[1, 2, 3], [4, 5, 6]])
        response = RpcResponse(id=id, result=result)

        assert response.id == id
        assert np.array_equal(response.result, result)

    def test_response_numpy_array_encode_decode(self):
        """Test that an RpcResponse with a numpy array result encodes and decodes correctly."""
        id = 2
        result = np.array([[1, 2, 3], [4, 5, 6]])
        response = RpcResponse(id=id, result=result)

        encoded = response.encode()
        decoded = RpcResponse.decode(encoded)

        assert decoded.id == id
        assert np.array_equal(decoded.result, result)

    def test_response_nested_array_result(self):
        """Test that an RpcResponse can be correctly initialised with a nested array result."""
        id = 2
        result = {"data": np.array([[1, 2, 3], [4, 5, 6]]), "status": "ok"}
        response = RpcResponse(id=id, result=result)

        encoded = response.encode()
        decoded = RpcResponse.decode(encoded)

        assert decoded.id == id
        assert np.array_equal(decoded.result["status"], result["status"])

    def test_response_numpy_array_decode_no_numpy(self, monkeypatch):
        """Test that decoding a response with a numpy array result raises an exception if numpy is
        not available.
        """
        import odin_sequencer.rpc.protocol

        id = 2
        result = np.array([[1, 2, 3], [4, 5, 6]])
        response = RpcResponse(id=id, result=result)
        encoded = response.encode()

        monkeypatch.setattr(odin_sequencer.rpc.protocol, "has_numpy", False)
        with pytest.raises(ValidationError):
            _ = RpcResponse.decode(encoded)

    def test_response_adapter_numpy_array_decode(self):
        """Test that the RpcResponseAdapter decodes a response with a numpy array result."""
        response_adapter = RpcResponseAdapter()
        array = np.array([[1, 2, 3], [4, 5, 6]])
        array_bytes = array.tobytes()
        array_b64 = base64.b64encode(array_bytes).decode("utf-8")
        response_bytes = (
            '{"jsonrpc":"2.0", "id": 4, "result": {'
            '    "type":"ndarray",'
            f'    "dtype": "{array.dtype.str}",'
            f'    "shape": {list(array.shape)},'
            f'    "data": "{array_b64}"'
            "}}"
        ).encode("utf-8")

        response = response_adapter.decode(response_bytes)

        assert isinstance(response, RpcResponse)
        assert np.array_equal(response.result, array)
