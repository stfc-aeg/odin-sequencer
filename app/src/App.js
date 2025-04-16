import Accordion from 'react-bootstrap/Accordion';
import { useState } from 'react';
import ModuleList from './components/ModuleList'
import { Col } from 'react-bootstrap';
import './SequenceCard.css';

import EndpointExamplePage from './components/EndpointExample';
import { OdinApp } from 'odin-react';

/*
  This is the main application for the React interface.
  It calls the ModuleList component from the components file, which in turn creates other components.
*/

const postPutMethod = () => {
  console.log("Post Message Method Called");
}

// const App = () => {


//   const postPutMethod = () => {
//     console.log("Post Message Method Called");
//   }

//   return (
//   <OdinApp title="Odin React Example"
//   navLinks={["Workshop", "With Endpoint Examples", "Graph Examples"]}
//   icon_src="odin.png"
//   icon_hover_src="prodin.png">
//     <EndpointExamplePage postPutMethod={postPutMethod}/>

//   </OdinApp> 
//   )
// }

// export default App



function BasicExample() {

  /*
  This constant has been created to imitate the object passed to it by the sequencer.
  It should, eventually, be changed to an adapter endpoint call.
  */

  const [sequence_modules, setSequenceModules] = useState (JSON.stringify({
    example_sequences: {
      test_sequence: {
        a_val: 123,
        b: "hello",
      },
      another_sequence: {
        c_val: 10,
        d: 20,
      },
      no_params: {

      },
      test: {
        num_numbers: 10,
      },
      abortable_sequence_test: {
        num_loops: 15,
        loop_delay: 4,
      },
    },
    qem_sequences: {
      CombineH5Files: {
        dirpath: "DIR_PATH",
      },
      GenerateVideo: {
        dirpath: "DIR_PATH",
      },
      averageADCValues: {
        dirpath: "DIR_PATH",
      },
      generateImages: {
        dirpath: "DIR_PATH",
      },
      plotcoarseMulti: {
        filepath: "DIR_PATH/combined_histograms.",
      },
    },
    spi_commands: {
      spi_read: {
        num_bytes: 38,
        vals: 64
      }, 
      spi_write: {
        abc : 20
      }
    }
  }))

  /* Returns a ModuleList, which is a component found in the 'components' folder */

  return (
    <>
      <Col sm={7}>
        <Accordion>
          <ModuleList sequence_modules={sequence_modules}></ModuleList>
        </Accordion>
      </Col>
      <pre class="pre-scrollable" id="log-messages"></pre>
      <EndpointExamplePage postPutMethod={postPutMethod}/>
    </>
  );



  return (
    <>
      <div class="col-md-7">
        <Col sm={7}>
          <Accordion>
            <ModuleList sequence_modules={sequence_modules}></ModuleList>
          </Accordion>
        </Col>
      </div>
      <div class="col-md-5">
        <pre class="pre-scrollable" id="log-messages"></pre>
      </div>
    </>
  );
}

export default BasicExample;

