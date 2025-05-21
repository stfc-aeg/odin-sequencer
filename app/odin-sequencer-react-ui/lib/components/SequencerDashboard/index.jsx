import { useRef, useEffect, useState } from 'react';
import ExecutionPanel from '../ExecutionPanel';
import SequenceTable from '../SequenceTable';

import sequencer_endpoint from "../sequencerEndpoint";
import MessageLog from '../MessageLog';

import './styles.css';


function BasicExample({ postPutMethod }) {
  const [sequenceModules, setSequenceModules] = useState({});
  const [error, setError] = useState({});
  const [abortDisabled, setAbortDisabled] = useState(true);

  const executionPanelRef = useRef(null);

  const fetchModules = () => {
    return sequencer_endpoint.get('')
      .then(result => {
        setSequenceModules(result.sequence_modules);
      })
      .catch(err => {
        console.error("Error fetching endpoint data:", err);
        setError(err.message);
      });
  };

  useEffect(() => {
    fetchModules();
  }, []);

  return (
    <>
      <div className="alert-box" id="alert-container"></div>
      <ExecutionPanel ref={executionPanelRef} abortDisabled={abortDisabled} setAbortDisabled={setAbortDisabled}></ExecutionPanel>
      <div className="flex-container">
        <div className="left">
          <SequenceTable fetchModules={fetchModules} sequenceModules={sequenceModules} executionPanelRef={executionPanelRef} setAbortDisabled={setAbortDisabled}></SequenceTable>
        </div>
        <div className="right">
          <MessageLog></MessageLog>
        </div>
      </div>
    </>
  );
}

export default BasicExample;
