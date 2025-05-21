import Accordion from 'react-bootstrap/Accordion'
import CardRow from '../CardRow'
import { Row } from 'react-bootstrap'

/* Constructs Accordion layer for each sequence module, then intialises the CardRow to display sequences. */

const SequenceModule = ({sequences, header, executionPanelRef, setAbortDisabled}) => {
    return (
        <Accordion.Item eventKey={header}>
            <Accordion.Header>{header}</Accordion.Header>
            <Accordion.Body>
                <Row>
                    <CardRow sequences={sequences} row_title={header} executionPanelRef={executionPanelRef} setAbortDisabled={setAbortDisabled}></CardRow>
                </Row>
            </Accordion.Body>
        </Accordion.Item>
    )
}

//Look into odin-react title card

export default SequenceModule