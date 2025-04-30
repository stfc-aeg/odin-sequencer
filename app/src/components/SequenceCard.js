import Card from 'react-bootstrap/Card'
import Button from 'react-bootstrap/Button'
import { useState, useRef } from 'react'
import { Modal } from 'react-bootstrap'
import ModalParams from './ModalParams'
import { useAdapterEndpoint } from 'odin-react';

/* Constructs a card for each sequence within the module */

const SequenceCard = ({ sequence, header, row_title }) => {
  const sequencer_endpoint = useAdapterEndpoint("odin_sequencer", "http://127.0.0.1:8888");
  const [showModal, setShowModal] = useState(false);
  const inputRefs = useRef(new Map());
  const readableHeader = String(header).replaceAll("_", " ")

  const handleOpenModal = () => setShowModal(true);
  const handleCloseModal = () => setShowModal(false);
  //const handleExecute = () => execute(sequence, header, sequencer_endpoint, row_title);

  const handleSave = () => {
    const updatedValues = {};
    inputRefs.current.forEach((ref, key) => {
      updatedValues[key] = ref.value;
    });
    console.log("Updated parameter values:", updatedValues);
    
    for (const key in updatedValues) {
      const paramPath = key.split('-');
      const paramName = paramPath[0];
      if (sequence[paramName]) {
        sequence[paramName].value = updatedValues[key]
      }
    }
    handleCloseModal();
  };

  const handleExecute = () => {
    if (Object.keys(sequence).length !== 0) {
      const data = get_input_parameter_values(sequence);
      sequencer_endpoint.put(data, `sequence_modules/${row_title}/${header}`)
        .then(() => {
          sequencer_endpoint.put({ 'execute': header })
            .catch(handleError);
        })
        .catch(handleError);
    } else {
      sequencer_endpoint.put({ 'execute': header }).catch(handleError);
    }
  };

  const handleError = (error) => {
    let message = error.message;
    if (message.startsWith('Invalid list')) {
      message = message.substring(message.lastIndexOf(':') + 2);
    } else if (message.startsWith('Type mismatch updating')) {
      const parts = message.split('/');
      const paramName = parts[parts.length - 2];
      message = `${paramName} - ${message.substring(message.lastIndexOf(':') + 2)}`;
    }
    console.log("error", message);
  };

  return (
    <>
      <Card>
        <Card.Body>
          <Card.Title>{readableHeader}</Card.Title>
          <Card.Text>
            <Button className="btn btn-info" onClick={handleOpenModal}>Parameters</Button>
            <Button className="btn btn-success btn-width execute-btn" onClick={handleExecute}>Execute</Button>
          </Card.Text>
        </Card.Body>
      </Card>

      <Modal show={showModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>{readableHeader}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ModalParams sequence={sequence} inputRefs={inputRefs} header={readableHeader}></ModalParams>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>
            Close
          </Button>
          <Button variant="primary" onClick={handleSave}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default SequenceCard;


/* 
function execute(params, seq_name, sequencer_endpoint, row_title) {
  if (Object.keys(params).length !== 0) {
    let data = get_input_parameter_values(params);

    sequencer_endpoint.put(data, `sequence_modules/${row_title}/${seq_name}`)
    .then(() => {
      console.log("sequencer", sequencer_endpoint);

      sequencer_endpoint.put({ 'execute': seq_name })
      .catch(error => {
        let alert_message = error.message;
        if (alert_message.startsWith('Invalid list')) {
          alert_message = alert_message.substring(alert_message.lastIndexOf(':') + 2);
        }

        console.log("first alert", alert_message)
      });
    })
    .catch(error => {
      let alert_message = error.message;
      if (alert_message.startsWith('Type mismatch updating')) {
        let last_slash = alert_message.lastIndexOf('/');
        let second_to_last_slash = alert_message.lastIndexOf('/', last_slash - 1);
        let param_name = alert_message.substring(second_to_last_slash + 1, last_slash);
        alert_message = `${param_name} - ${alert_message.substring(alert_message.lastIndexOf(':') + 2)}`;
      }

      console.log("second alert", alert_message)
    });

  } else {
    sequencer_endpoint.put({ 'execute': seq_name })
    .catch(error => {
      let alert_message = error.message;
      console.log("third alert", alert_message)
    });
  }
}
 */


function get_input_parameter_values(params, seq) {
  let data = {};
  for (const param in params) {
    let param_val = String(params[param].value);
    let param_type = params[param].type;

    if (param_type != 'str') {
        param_val = parse_parameter_value(param_val, param_type);
    }

    data[param] = { 'value': param_val };
  }

  return data;
}

function parse_parameter_value(param_val, param_type) {
  if (param_type.startsWith('list')) {
      const element_type = param_type.split("list-");
      param_val = param_val.split(',');

      return param_val.map(function (element) {
          return parse_parameter_value(element.trim(), element_type[1]);
      })
  }

  switch (param_type) {
      case 'int':
          param_val = parseInt(param_val);
          break;
      case 'float':
          param_val = parseFloat(param_val);
          break;
      case 'bool':
          param_val = param_val.toLowerCase() == 'true';
          break;
  }

  return param_val;
}
