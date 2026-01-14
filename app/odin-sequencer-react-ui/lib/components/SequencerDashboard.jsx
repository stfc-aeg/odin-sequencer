import { useRef, useEffect, useState } from 'react';
import { Row, Col } from 'react-bootstrap';
import ExecutionPanel from './ExecutionPanel';
import SequenceTable from './SequenceTable';

import MessageLog from './MessageLog';

function BasicExample({ sequencer_endpoint }) {
  const [sequenceModules, setSequenceModules] = useState({});
  const [error, setError] = useState({});
  const [abortDisabled, setAbortDisabled] = useState(true);

  const executionPanelRef = useRef(null);

  const fetchModules = () => {
    return sequencer_endpoint.get('')
      .then(result => {
        setSequenceModules(result.sequence_modules);
      })
      .catch(err => {
        console.error("Error fetching endpoint data:", err);
        setError(err.message);
      });
  };

  useEffect(() => {
    fetchModules();
  }, []);

  return (
    <Col>
      <Row>
        <ExecutionPanel
          ref={executionPanelRef}
          abortDisabled={abortDisabled}
          setAbortDisabled={setAbortDisabled}
          sequencer_endpoint={sequencer_endpoint}
        />
      </Row>
      <Row>
        <Col xs={12} lg={6}>
          <SequenceTable
            fetchModules={fetchModules}
            sequenceModules={sequenceModules}
            executionPanelRef={executionPanelRef}
            setAbortDisabled={setAbortDisabled}
            sequencer_endpoint={sequencer_endpoint}
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
