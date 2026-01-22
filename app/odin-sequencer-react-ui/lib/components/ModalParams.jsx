import { Row , Col, Form } from "react-bootstrap"
import { WithEndpoint } from "odin-react";

/* Constructing the labels and input boxes for the parameters inside the modal. */
const EndpointFormControl = WithEndpoint(Form.Control);

function ModalParams ({endpoint, sequence, sequenceName, sequenceFile}) {
  return (
    <Form>
      {Object.entries(sequence).map(([paramKey, param]) => {
        const paramLabel = `${paramKey.replaceAll(' ', '_')}-${param.type}`;
        const paramName = `${paramKey.replaceAll(' ', '_')} (${param.type})`;

        return (
          <Form.Group as={Row} className="mb-2" key={paramLabel}>
            <Form.Label column sm={5}>
              {paramName}
            </Form.Label>
            <Col sm={7}>
              <EndpointFormControl
                endpoint={endpoint}
                fullpath={`sequence_modules/${sequenceFile}/${sequenceName}/${paramKey}/value`}
              />
            </Col>
          </Form.Group>
        );
      })}
    </Form>
  )
}

export default ModalParams