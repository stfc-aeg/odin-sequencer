import SequenceModule from '../SequenceModule'
import Accordion from 'react-bootstrap/Accordion';

/* Initialises a SequenceModule component for each module found in the object. */

const ModuleList = ({sequence_modules, executionPanelRef, setAbortDisabled, sequencer_endpoint}) => {

    sequence_modules = Object.fromEntries(Object.entries(sequence_modules).sort());

    //const sequences_modules_obj = JSON.parse(sequence_modules)
    const sequences_modules_obj = sequence_modules

    const listHeaders = Object.entries(sequences_modules_obj).flatMap(([moduleKey,sequences]) =>
        <SequenceModule key={moduleKey} header={moduleKey} sequences={JSON.stringify(sequences)} executionPanelRef={executionPanelRef} setAbortDisabled={setAbortDisabled} sequencer_endpoint={sequencer_endpoint}></SequenceModule>
    )

    return (
        <Accordion alwaysOpen>
          {listHeaders}
        </Accordion>
      );
}

export default ModuleList