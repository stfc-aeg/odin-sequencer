import { Row, Col } from 'react-bootstrap';
import ExecutionPanel from './ExecutionPanel';
import SequenceTable from './SequenceTable';

import MessageLog from './MessageLog';

function BasicExample({ endpoint }) {

  return (
    <Col>
      <Row>
        <ExecutionPanel
          endpoint={endpoint}
        />
      </Row>
      <Row>
        <Col xs={12} lg={6}>
          <SequenceTable
            endpoint={endpoint}
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
