import { Button, Form, Stack } from 'react-bootstrap';
import { WithEndpoint } from 'odin-react';

const EndpointCheck = WithEndpoint(Form.Check);
const EndpointButton = WithEndpoint(Button);

// The optional onReload function here should simply 
const SequenceButtons = ({ endpoint, onReload }) => {

    return (
      <Form>
        <Stack direction="horizontal" gap={3} className="justify-content-end">
          <EndpointCheck
            endpoint={endpoint}
            fullpath="detect_module_modifications"
            type="switch"
            label="Detect Changes"
          />
          <EndpointButton
            endpoint={endpoint}
            fullpath="reload/execute"
            value={true}
            post_method={onReload}
          >
            Reload
          </EndpointButton>
        </Stack>
      </Form>
    );
};

export default SequenceButtons;
