import { useState } from 'react'
import { Button, Modal, Col, Row } from 'react-bootstrap';
import { TitleCard, WithEndpoint } from 'odin-react';
import ModalParams from './ModalParams'

/* Constructs a card for each sequence within the module */

const EndpointButton = WithEndpoint(Button);

const SequenceCard = ({ endpoint, moduleName, sequenceName, sequenceConfig }) => {
  const [showModal, setShowModal] = useState(false);
  const readableSeqName = String(sequenceName).replaceAll("_", " ");

  const handleOpenModal = () => setShowModal(true);
  const handleCloseModal = () => setShowModal(false);

  return (
    <TitleCard title={readableSeqName}>
      <Row className="justify-content-md-centre">
        <Col>
          <Button
            className="mb-2 w-100"
            variant="secondary"
            onClick={handleOpenModal}
          >
            Parameters
          </Button>
        </Col>
        <Col>
          <EndpointButton
            endpoint={endpoint}
            fullpath={"execute"}
            variant="primary"
            className="w-100"
            value={sequenceName}
          >
            Execute
          </EndpointButton>
        </Col>
      </Row>

      <Modal show={showModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>{readableSeqName}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ModalParams 
            endpoint={endpoint}
            sequenceConfig={sequenceConfig}
            moduleName={moduleName}
            sequenceName={sequenceName}
          />
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </TitleCard>
  );
};

export default SequenceCard;
