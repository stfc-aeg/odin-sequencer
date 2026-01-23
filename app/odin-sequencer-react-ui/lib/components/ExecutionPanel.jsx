// import { useRef, useImperativeHandle, forwardRef } from 'react';
// import { handleAlerts } from './alertUtils';

import { useEffect, useState } from 'react';
import { ProgressBar, Spinner, Button } from 'react-bootstrap';
import { TitleCard } from 'odin-react';
import { handleAlerts } from './alertUtils';

function ExecutionPanel({ endpoint}) {
  const [abortDisabled, setAbortDisabled] = useState(true);

  const isExecuting = endpoint.data?.is_executing;
  const progress = endpoint.data?.execution_progress;

  // Pretty reading of module and sequence name without needing args or refs passed around
  const parseExecutePath = (execute) => {
    if (!execute || typeof execute !== 'string') { return { module: '', sequence: '' }; }
    // Execute should look like module_name/sequence_name
    const parts = execute.split('/');
    const module = parts[0]?.replaceAll('_', ' ') ?? '';
    const sequence = parts[1]?.replaceAll('_', ' ') ?? '';

    return { module, sequence };
  }

  const { module, sequence } = parseExecutePath(endpoint.data?.execute);

  // abort button handling
  useEffect(() => {
    if (isExecuting === true) setAbortDisabled(false);
    if (isExecuting === false) setAbortDisabled(true);
  }, [isExecuting, setAbortDisabled]);

  const abortSequence = () => {
    endpoint
      .put({ abort: true })
      .then(() => {
        handleAlerts({
          alert_message: 'Abort sent to currently executing sequence',
          alert_type: 'primary'
        });
      })
      .catch(error => {
        handleAlerts({
          alert_message: error.message,
          alert_type: 'error'
        });
      });
  };

  if (!isExecuting) return null;

  let percent = 0;
  let label = '';

  if (progress) {
    if (progress.total > 0) {
      percent = Math.floor((100*progress.current) / progress.total);
      label = `(${progress.current}/${progress.total})`;
    }
    else {
      percent = 100;
    }
  }

  return (
    <TitleCard title={`${module} | ${sequence}`} className="mb-3">

      <div className="d-flex justify-content-between align-items-center mb-2">
        <div>
          <strong>Executing sequence '{sequence}'</strong>
          <Spinner
            animation="border"
            size="sm"
            className="ms-2"
          />
          <div className="text-muted">{label}</div>
        </div>
        {!abortDisabled && (
          <Button variant="primary" onClick={abortSequence}>
            Abort
          </Button>
        )}
      </div>
      <ProgressBar
        animated
        striped
        now={percent}
        style={{ height: '12px' }}
      />
    </TitleCard>
  )
}

export default ExecutionPanel;
