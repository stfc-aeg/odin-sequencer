import { TitleCard } from 'odin-react';
import { Form, Col } from 'react-bootstrap';

const MessageLog = () => {
  return (
    <TitleCard title="Log Messages">
    <Col>
      <Form.Control
        as="textarea"
        readOnly
        id="log-messages"
        style={{
          height:'600px',
          overflowY:'auto',
          resize:'none',
          whiteSpace:'pre-wrap',
          fontFamily:'monospace',
          backgroundColor:'#f7f7f7',
          border:'1px solid #ccc'
        }}
      />
      </Col>
    </TitleCard>
  )
}

export default MessageLog
