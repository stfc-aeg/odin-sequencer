import { useEffect, useState } from 'react';
import Alert from 'react-bootstrap/Alert';
import Fade from 'react-bootstrap/Fade';

// This function shows an alert indicating if the reload was successful
// As such, it requires a prop that is updated when you reload the sequencer (see SequenceButtons)
// Without this, it cannot know if it has updated or not as polling the endpoint will show the 
// display at all times, which is not correct.
function ReloadUpdate({ endpoint, reloadTrigger }) {

  const isSuccess = endpoint.data?.reload?.success;
  const status = endpoint.data?.reload?.status;

  const [open, setOpen] = useState(false);
  const [lastTrigger, setLastTrigger] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Only do anything if trigger has changed
    if (reloadTrigger === lastTrigger) return; 

    setVisible(true);
    setOpen(true);
    setLastTrigger(reloadTrigger);

    let timer;
    if (isSuccess) {
      timer = setTimeout(() => {
        setOpen(false);  // Fade out
        setTimeout(() => setVisible(false), 250);
      }, 5000);
    }

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [reloadTrigger, isSuccess]);

  if (!visible) return null;

  return (
    <Fade in={open} out={!open}>
      <div>
        <Alert
          variant={isSuccess ? 'success':'danger'}
          dismissible={!isSuccess}
          onClose={() => {setOpen(false); setVisible(false); } }
          className="mt-2 w-100"
        >
          {status}
        </Alert>
      </div>
    </Fade>
  )
}

export default ReloadUpdate;
