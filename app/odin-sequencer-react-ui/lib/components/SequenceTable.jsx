import Accordion from 'react-bootstrap/Accordion';
import ModuleList from './ModuleList'
import SequenceButtons from './SequenceButtons'
import { Col, Row } from 'react-bootstrap';
import { TitleCard } from 'odin-react';

const SequenceTable = ({ endpoint, executionPanelRef, setAbortDisabled }) => {
  return (
    <TitleCard title={
      <Row>
        <Col xs={3} className="d-flex align-items-center" style={{fonstSize:'1.3rem'}}>Sequences</Col>
        <Col xs={9}><SequenceButtons endpoint={endpoint}/></Col>
      </Row>
    }>
      <Col>
        <Accordion>
          <ModuleList
            endpoint={endpoint}
            executionPanelRef={executionPanelRef}
            setAbortDisabled={setAbortDisabled}
          />
        </Accordion>
      </Col>
    </TitleCard>
  )
}

export default SequenceTable
