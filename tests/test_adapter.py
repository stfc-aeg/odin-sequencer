import json

from unittest.mock import Mock, MagicMock, patch

from odin.adapters.parameter_tree import ParameterTreeError
from odin_sequencer import CommandSequenceError
from src.odin_sequencer.adapter import CommandSequenceManagerAdapter


class TestCommandSequenceManagerAdapter:

    @classmethod
    def setup_class(cls):
        cls.adapter = CommandSequenceManagerAdapter()
        cls.command_sequencer_mock = MagicMock()
        cls.adapter.command_sequencer = cls.command_sequencer_mock
        cls.request = Mock()
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def test_get_valid_path(self):
        self.command_sequencer_mock.get.return_value = {'key': 'value'}

        response = self.adapter.get('', self.request)

        assert response.status_code == 200
        assert type(response.data) == dict
        assert 'key' in response.data

        self.command_sequencer_mock.get.reset_mock(return_value=True, side_effect=True)

    def test_get_invalid_path(self):
        invalid_path = 'invalid_path'
        self.command_sequencer_mock.get.side_effect = ParameterTreeError(
            'Invalid path: {}'.format(invalid_path))

        response = self.adapter.get('invalid/path', self.request)

        assert response.status_code == 400
        assert 'error' in response.data
        assert response.data['error'] == 'Invalid path: {}'.format(invalid_path)

        self.command_sequencer_mock.get.reset_mock(return_value=True, side_effect=True)

    def test_put_valid_path(self):
        self.command_sequencer_mock.get.return_value = {'key': 'value'}
        request_body = {'key': 'value'}
        self.request.body = json.dumps(request_body)

        response = self.adapter.put('', self.request)

        assert response.status_code == 200
        assert type(response.data) == dict
        assert 'key' in response.data
        self.command_sequencer_mock.get.assert_called_once_with('')

        self.command_sequencer_mock.get.reset_mock(return_value=True, side_effect=True)

    def test_put_invalid_path(self):
        invalid_path = 'invalid_path'
        self.command_sequencer_mock.set.side_effect = CommandSequenceError(
            'Invalid path: {}'.format(invalid_path))
        request_body = {'key': 'value'}
        self.request.body = json.dumps(request_body)

        response = self.adapter.put(invalid_path, self.request)

        assert response.status_code == 400
        assert 'error' in response.data
        assert response.data['error'] == 'Invalid path: {}'.format(invalid_path)
        self.command_sequencer_mock.get.assert_not_called()

        self.command_sequencer_mock.set.reset_mock(return_value=True, side_effect=True)

    @patch('src.odin_sequencer.adapter.json_decode')
    def test_put_bad_request(self, json_decode_mock):
        type_error_message = 'No JSON object could be decoded'
        json_decode_mock.side_effect = TypeError(type_error_message)

        self.request.body = 'json as string'

        response = self.adapter.put('', self.request)

        assert response.status_code == 400
        assert 'error' in response.data
        assert response.data['error'] == 'Failed to decode PUT request body: {}'.format(
            type_error_message)
        self.command_sequencer_mock.set.assert_not_called()

        json_decode_mock.reset_mock(return_value=True, side_effect=True)
