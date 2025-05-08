import Accordion from 'react-bootstrap/Accordion';
import { useEffect, useState } from 'react';
import ModuleList from './components/ModuleList'
import MessageLog from './components/MessageLog'
import { Col } from 'react-bootstrap';
import './SequenceCard.css';

import { AdapterEndpoint } from './components/AdapterEndpointWrapper';
import { useAdapterEndpoint } from 'odin-react';

/*
  This is the main application for the React interface.
  It calls the ModuleList component from the components file, which in turn creates other components.
*/



const ENDPOINT_URL = "http://127.0.0.1:8888";

function BasicExample({ postPutMethod }) {
  const [sequenceModules, setSequenceModules] = useState({});
  const [error, setError] = useState({});
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
          <Col sm={7}>
            <Accordion>
              <ModuleList sequence_modules={sequenceModules}></ModuleList>
            </Accordion>
          </Col>
        </div>
        <div class="right">
          <MessageLog reloadModules={fetchModules}></MessageLog>
        </div>
      </div>
    </>
  );
}

export default BasicExample;
