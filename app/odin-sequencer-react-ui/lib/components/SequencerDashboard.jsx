import { useRef, useEffect, useState } from 'react';
import { Row, Col } from 'react-bootstrap';
import ExecutionPanel from './ExecutionPanel';
import SequenceTable from './SequenceTable';

import MessageLog from './MessageLog';

function BasicExample({ endpoint }) {
  const [abortDisabled, setAbortDisabled] = useState(true);

  const executionPanelRef = useRef(null);

  return (
    <Col>
      <Row>
        <ExecutionPanel
          ref={executionPanelRef}
          abortDisabled={abortDisabled}
          setAbortDisabled={setAbortDisabled}
          endpoint={endpoint}
        />
      </Row>
      <Row>
        <Col xs={12} lg={6}>
          <SequenceTable
            endpoint={endpoint}
            executionPanelRef={executionPanelRef}
            setAbortDisabled={setAbortDisabled}
          />
        </Col>
        <Col xs={12} lg={6}>
          <MessageLog/>
        </Col>
      </Row>
    </Col>
  );
}

export default BasicExample;
