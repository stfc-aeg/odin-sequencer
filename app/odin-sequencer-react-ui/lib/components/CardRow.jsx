import SequenceCard from "./SequenceCard";
import { Col } from "react-bootstrap";

/* Creates a row within the accordion, for each sequence to go into. */

const CardRow = ({ endpoint, sequences, moduleName }) => {

  const sequenceEntries = Object.entries(sequences);

  const cards = sequenceEntries.map(([sequenceName, sequenceConfig]) => (
    <Col key={sequenceName} xs={4} className="mb-2">
      <SequenceCard
        endpoint={endpoint}
        moduleName={moduleName}
        sequenceName={sequenceName}
        sequenceConfig={sequenceConfig}
      />
    </Col>
  ));  

  return (cards)
};

export default CardRow;