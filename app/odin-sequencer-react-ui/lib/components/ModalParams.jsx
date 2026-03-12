import { Row , Col, Form } from "react-bootstrap"
import { WithEndpoint } from "odin-react";

/* Constructing the labels and input boxes for the parameters inside the modal. */
const EndpointFormControl = WithEndpoint(Form.Control);
const EndpointFormCheck = WithEndpoint(Form.Check);

function ModalParams ({endpoint, sequenceConfig, sequenceName, moduleName}) {
  return (
    <Form>
      {Object.entries(sequenceConfig).map(([paramKey, param]) => {
        const paramLabel = `${paramKey.replaceAll(' ', '_')}-${param.type}`;
        const paramName = `${paramKey.replaceAll(' ', '_')} (${param.type})`;

        return (
          <Form.Group as={Row} className="mb-2 d-flex align-items-stretch" key={paramLabel}>
            <Form.Label column sm={5}>
              {paramName}
            </Form.Label>
            <Col sm={7}>
              {
                // Check if the type of the endpoint is boolean. If it is, render a toggle switch instead of a formcontrol
                param.type === 'bool' ? 
                  <EndpointFormCheck
                    type="switch"
                    endpoint={endpoint}
                    fullpath={`sequence_modules/${moduleName}/${sequenceName}/${paramKey}/value`}
                    className="w-100 h-100 d-flex align-items-center"
                  />
                :
                  <EndpointFormControl
                    endpoint={endpoint}
                    fullpath={`sequence_modules/${moduleName}/${sequenceName}/${paramKey}/value`}
                  />
              }
            </Col>
          </Form.Group>
        );
      })}
    </Form>
  )
}

export default ModalParams