import Accordion from 'react-bootstrap/Accordion'
import CardRow from './CardRow'
import { Row } from 'react-bootstrap'

/* Constructs Accordion layer for each sequence module, then intialises the CardRow to display sequences. */

const SequenceModule = ({ endpoint, moduleName, sequences }) => {
  return (
    <Accordion.Item eventKey={moduleName}>
      <Accordion.Header>{moduleName}</Accordion.Header>
      <Accordion.Body>
        <Row>
          <CardRow
            endpoint={endpoint}
            sequences={sequences}
            moduleName={moduleName}
          />
        </Row>
      </Accordion.Body>
    </Accordion.Item>
  )
}

//Look into odin-react title card

export default SequenceModule