import SequenceModule from './SequenceModule'
import Accordion from 'react-bootstrap/Accordion';

/* Initialises a SequenceModule component for each module found in the object. */

const ModuleList = ({ endpoint }) => {

    const sequenceModules = endpoint.data?.sequence_modules ?? {};
    const sortedModules = Object.entries(sequenceModules).sort(
      ([a], [b]) => a.localeCompare(b)
    )

    return (
      <Accordion alwaysOpen>
        {sortedModules.map(([moduleName, sequences]) => (
            <SequenceModule
              endpoint={endpoint}
              key={moduleName}
              moduleName={moduleName}
              sequences={sequences}
            />
          ))
        }
      </Accordion>
      );
}

export default ModuleList