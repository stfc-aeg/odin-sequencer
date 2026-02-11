import { Row, Col } from 'react-bootstrap';
import { useState } from 'react';
import ExecutionPanel from './ExecutionPanel';
import SequenceTable from './SequenceTable';
import ReloadUpdate from './ReloadUpdate';
import ModuleModificationsDetected from './ModuleModificationsDetected';

import MessageLog from './MessageLog';

function BasicExample({ endpoint }) {

  // For the benefit of ReloadUpdate knowing when a trigger has changed
  const [reloadTrigger, setReloadTrigger] = useState(0);

  return (
    <Col>
      <Row>
        <ExecutionPanel
          endpoint={endpoint}
        />
        <ReloadUpdate
          endpoint={endpoint}
          reloadTrigger={reloadTrigger}
        />
        <ModuleModificationsDetected
          endpoint={endpoint}
        />
      </Row>
      <Row>
        <Col xs={12} lg={6}>
          <SequenceTable
            endpoint={endpoint}
            onReload={() => setReloadTrigger(prev => prev+1)}
          />
        </Col>
        <Col xs={12} lg={6}>
          <MessageLog endpoint={endpoint}/>
        </Col>
      </Row>
    </Col>
  );
}

export default BasicExample;
