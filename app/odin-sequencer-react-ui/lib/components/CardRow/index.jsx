import SequenceCard from "../SequenceCard";
import { Col } from "react-bootstrap";

/* Creates a row within the accordion, for each sequence to go into. */

const CardRow = ({sequences, row_title, executionPanelRef, setAbortDisabled, sequencer_endpoint}) => {
  sequences = JSON.parse(sequences)
  const listItems = (Object.entries(sequences)).flatMap(([sequenceKey, sequence]) =>
    <Col xs={4} className="mb-2">
      <SequenceCard
        key={sequenceKey}
        header={sequenceKey}
        sequence={sequence}
        row_title={row_title}
        executionPanelRef={executionPanelRef}
        setAbortDisabled={setAbortDisabled}
        sequencer_endpoint={sequencer_endpoint}
      />
    </Col>
  );
  return (listItems)
};

export default CardRow;