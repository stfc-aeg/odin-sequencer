import { useState, useRef, useEffect } from 'react'
import { Button, Modal, Col, Row } from 'react-bootstrap';
import { TitleCard, WithEndpoint } from 'odin-react';
import ModalParams from './ModalParams'
import { handleAlerts } from './alertUtils';
import { useMessageLog, awaitExecutionComplete, awaitProcessExecutionComplete } from './useMessageLog';

/* Constructs a card for each sequence within the module */

const EndpointButton = WithEndpoint(Button);

const SequenceCard = ({ sequence, sequenceName, sequenceFile, executionPanelRef, setAbortDisabled, sequencer_endpoint }) => {
  const { displayLogMessages } = useMessageLog({ sequencer_endpoint });
  const [showModal, setShowModal] = useState(false);
  const readableSeqName = String(sequenceName).replaceAll("_", " ");

  const handleOpenModal = () => setShowModal(true);
  const handleCloseModal = () => setShowModal(false);

  // useEffect to run displayExecution when execution starts
  useEffect(() => {
    if (sequencer_endpoint.data?.is_executing && executionPanelRef.current) {
      executionPanelRef.current?.displayExecution?.(sequenceName);
    }
  }, [sequencer_endpoint.data?.is_executing]); // Runs when endpoint indicates sequence is executing


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
            endpoint={sequencer_endpoint}
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
            endpoint={sequencer_endpoint}
            sequence={sequence}
            sequenceFile={sequenceFile}
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
