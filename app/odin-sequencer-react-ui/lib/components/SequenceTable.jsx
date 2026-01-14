import Accordion from 'react-bootstrap/Accordion';
import ModuleList from './ModuleList'
import SequenceButtons from './SequenceButtons'
import { Col, Row, Card } from 'react-bootstrap';
import { TitleCard } from 'odin-react';

const SequenceTable = ({ fetchModules, sequenceModules, executionPanelRef, setAbortDisabled, sequencer_endpoint }) => {
  return (
    <TitleCard title={
      <Row>
        <Col xs={3} className="d-flex align-items-center" style={{fonstSize:'1.3rem'}}>Sequences</Col>
        <Col xs={9}><SequenceButtons reloadModules={fetchModules} executionPanelRef={executionPanelRef} setAbortDisabled={setAbortDisabled} sequencer_endpoint={sequencer_endpoint}/></Col>
      </Row>
    }>
      <Col>
        <Accordion>
          <ModuleList
            sequence_modules={sequenceModules}
            executionPanelRef={executionPanelRef}
            setAbortDisabled={setAbortDisabled}
            sequencer_endpoint={sequencer_endpoint}
          />
        </Accordion>
      </Col>
    </TitleCard>
  )
}

export default SequenceTable
