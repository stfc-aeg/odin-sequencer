import { Row , Col, Form } from "react-bootstrap"

/* Constructing the labels and input boxes for the parameters inside the modal. */

const ModalParams = ({sequence, inputRefs}) => {
  return (
    <Form>
      {Object.entries(sequence).map(([paramKey, param]) => {
        const paramLabel = `${paramKey.replaceAll(' ', '_')}-${param.type}`;
        const paramName = `${paramKey.replaceAll(' ', '_')} (${param.type})`;
        const paramValue = param.value !== param.default ? param.value : param.default;
        const inputRef = (el) => {
          if (el) inputRefs.current.set(paramLabel, el);
        };
        return (
          <Form.Group as={Row} className="mb-2" key={paramLabel}>
            <Form.Label column sm={5}>
              {paramName}
            </Form.Label>
            <Col sm={7}>
              <Form.Control
                type="text"
                defaultValue={paramValue}
                ref={inputRef}
              />
            </Col>
          </Form.Group>
        );
      })}
    </Form>
  )
}

export default ModalParams