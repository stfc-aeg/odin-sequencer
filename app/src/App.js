import Accordion from 'react-bootstrap/Accordion';
import { useRef, useEffect, useState } from 'react';
import ModuleList from './components/ModuleList'
import SequenceButtons from './components/SequenceButtons'
import { Col } from 'react-bootstrap';
//import './SequenceCard.css';
import './App.css';
import ExecutionPanel from './components/ExecutionPanel';

import { AdapterEndpoint } from './components/AdapterEndpointWrapper';
import { useAdapterEndpoint } from 'odin-react';
import MessageLog from './components/MessageLog';

/*
  This is the main application for the React interface.
  It calls the ModuleList component from the components file, which in turn creates other components.
*/



const ENDPOINT_URL = "http://127.0.0.1:8888";

function BasicExample({ postPutMethod }) {
  const [sequenceModules, setSequenceModules] = useState({});
  const [error, setError] = useState({});
  const [abortDisabled, setAbortDisabled] = useState(true);

  const executionPanelRef = useRef(null);
  //const sequencer_endpoint = useAdapterEndpoint("odin_sequencer", ENDPOINT_URL);
  const sequencer_endpoint = new AdapterEndpoint("odin_sequencer", ENDPOINT_URL);

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
      <div class="alert-box" id="alert-container"></div>
      <div class="flex-container">
        <div class="left">
          <SequenceButtons reloadModules={fetchModules} executionPanelRef={executionPanelRef} setAbortDisabled={setAbortDisabled}></SequenceButtons>
          <ExecutionPanel ref={executionPanelRef} abortDisabled={abortDisabled} setAbortDisabled={setAbortDisabled}></ExecutionPanel>
          <Col sm={7}>
            <Accordion>
              <ModuleList sequence_modules={sequenceModules} executionPanelRef={executionPanelRef} setAbortDisabled={setAbortDisabled}></ModuleList>
            </Accordion>
          </Col>
        </div>
        <div class="right">
          <MessageLog></MessageLog>
        </div>
      </div>
    </>
  );
}

export default BasicExample;
