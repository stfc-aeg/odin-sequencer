import { useEffect, useState } from 'react';
import Alert from 'react-bootstrap/Alert';
import Fade from 'react-bootstrap/Fade';

// This function shows an alert indicating if the reload was successful
// As such, it requires a prop that is updated when you reload the sequencer (see SequenceButtons)
// Without this, it cannot know if it has updated or not as polling the endpoint will show the 
// display at all times, which is not correct.
function ModuleModificationsDetected({ endpoint }) {

  const isModified = endpoint.data?.module_modifications_detected;

  const [hide, setHide] = useState(false);

  useEffect(() => {
    setHide(isModified);
  }, [isModified])

  if (!hide) return null;

  return (
    <Fade in={isModified} out={!isModified}>
      <div>
        <Alert
          variant='warning'
          dismissible={() => setHide(true) }
          className="mt-2 w-100"
        >
          Code changes were detected, click the reload button to load them.
        </Alert>
      </div>
    </Fade>
  )
}

export default ModuleModificationsDetected;
