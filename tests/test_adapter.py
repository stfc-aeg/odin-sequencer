import json

from unittest.mock import Mock, MagicMock, patch

from odin_sequencer import SequencerError
from src.odin_sequencer.adapter import SequencerAdapter
import pytest

@pytest.fixture
def context_object():
    """
    Test fixture for creating a simple container object that can be loaded into
    the sequence manager context and accessed for test.
    """

    class ContextObject():
        """An example of a context object"""

        def __init__(self, value):
            self.value = value

        def increment(self, val):
            """Increments a given value by 1"""
            return val + 1

    return ContextObject(255374)

class TestSequencerAdapter:

    @classmethod
    def setup_class(cls):
        cls.adapter = SequencerAdapter()
        cls.controller_mock = MagicMock()
        cls.adapter.controller = cls.controller_mock
        cls.request = Mock()
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        cls.request.query_arguments = {}

    def test_get_valid_path(self):
        self.controller_mock.get.return_value = {'key': 'value'}

        response = self.adapter.get('', self.request)

        assert response.status_code == 200
        assert type(response.data) == dict
        assert 'key' in response.data

        self.controller_mock.get.reset_mock(return_value=True, side_effect=True)

    def test_get_invalid_path(self):
        invalid_path = 'invalid_path'
        self.controller_mock.get.side_effect = SequencerError(
            'Invalid path: {}'.format(invalid_path))

        response = self.adapter.get('invalid/path', self.request)

        assert response.status_code == 400
        assert 'error' in response.data
        assert response.data['error'] == 'Invalid path: {}'.format(invalid_path)

        self.controller_mock.get.reset_mock(return_value=True, side_effect=True)

    def test_put_valid_path(self):
        self.controller_mock.get.return_value = {'key': 'value'}
        request_body = {'key': 'value'}
        self.request.body = json.dumps(request_body)

        response = self.adapter.put('', self.request)

        assert response.status_code == 200
        assert type(response.data) == dict
        assert 'key' in response.data
        self.controller_mock.get.assert_called_once_with('')

        self.controller_mock.get.reset_mock(return_value=True, side_effect=True)

    def test_put_invalid_path(self):
        invalid_path = 'invalid_path'
        self.controller_mock.set.side_effect = SequencerError(
            'Invalid path: {}'.format(invalid_path))
        request_body = {'key': 'value'}
        self.request.body = json.dumps(request_body)

        response = self.adapter.put(invalid_path, self.request)

        assert response.status_code == 400
        assert 'error' in response.data
        assert response.data['error'] == 'Invalid path: {}'.format(invalid_path)
        self.controller_mock.get.assert_not_called()

        self.controller_mock.set.reset_mock(return_value=True, side_effect=True)

    def test_add_context(self, context_object):

        obj_name = 'context_object'
        self.adapter.add_context(obj_name, context_object)
        
        self.controller_mock._add_context.assert_called_once_with(obj_name, context_object)
        self.controller_mock.get.reset_mock(return_value=True, side_effect=True)
