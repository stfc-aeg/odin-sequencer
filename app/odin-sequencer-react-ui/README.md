# odin-sequencer-react-ui

React component library for integrating with the [ODIN Sequencer](https://github.com/stfc-aeg/odin-sequencer). Provides a reusable UI dashboard and components for building and controlling sequences.

## Installation

Add to your `package.json` dependencies:

```json
"dependencies": {
  "bootstrap": "^5.3.6",
  "odin-react": "github:stfc-aeg/odin-react",
  "react": "^18.3.1",
  "react-bootstrap": "^2.10.10",
  "react-dom": "^18.3.1",
  "odin-sequencer-react-ui": "github:stfc-aeg/odin-sequencer-ui"
}
```

Then install using `npm install`


## Basic Usage

import components individually

```js
import {
  OdinSequencer,
  ExecutionPanel,
  MessageLog,
  ModuleList,
  SequenceButtons,
  SequenceTable
} from 'odin-sequencer-react-ui';
```

Ensure Bootstrap CSS is available in your app (either top level or where you use the sequencer components)

```js
import 'bootstrap/dist/css/bootstrap.min.css'
```

### Connecting to the sequencer endpoint

When constructing sequencer_endpoint, you will notice `import.meta.env.VITE_SEQUENCER_ENDPOINT_URL`. This is a Vite reference to a .env file that looks something like this:
`VITE_SEQUENCER_ENDPOINT_URL=URL` where URL is the URL of the sequencer endpoint.
If you are not using Vite, you can either replace the import.meta.env with the URL or use .env with `process.env.VITE_SEQUENCER_ENDPOINT_URL`

.env files go in the root of the app you are using this library in. They can have .local at the end and you can add *.local if you do not want to accidentally commit it.


## Examples

### OdinSequencer module example
```js
import { useAdapterEndpoint } from 'odin-react';
import { OdinSequencer } from 'odin-sequencer-react-ui';

function App() {
  const sequencer_endpoint = useAdapterEndpoint("odin_sequencer", import.meta.env.VITE_SEQUENCER_ENDPOINT_URL);
  return (
    <>
      <p>
        (page loaded successfully)
      </p>
      <OdinSequencer sequencer_endpoint={sequencer_endpoint} />
    </>
  )
}

export default App
```

Using this module will import the entire Odin Sequencer UI with all of its functionality. You will not need to include anything other than this. This is the recommended use case as you can place the sequencer as a page in an OdinApp UI. This is simpler than constructing it yourself.


### Seperate structured example
```js
import { useRef, useEffect, useState } from 'react';
import { useAdapterEndpoint } from 'odin-react';
import { SequenceTable, ExecutionPanel, MessageLog } from 'odin-sequencer-react-ui';

function App() {

  const sequencer_endpoint = useAdapterEndpoint("odin_sequencer", import.meta.env.VITE_SEQUENCER_ENDPOINT_URL);

  const [sequenceModules, setSequenceModules] = useState({});
  const executionPanelRef = useRef(null);
  const [abortDisabled, setAbortDisabled] = useState(true);

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
  }, [])

  return (
    <>
      <p>
        (page loaded successfully)
      </p>
      <div className="alert-box" id="alert-container"></div>
      <ExecutionPanel endpoint={endpoint} />
      <MessageLog endpoint={endpoint}/>
      <SequenceTable endpoint={endpoint} />
    </>
  )
}

export default App
```
<img src="example/example_screenshots/seperate_structured.png" alt="Web page view of example above" width="700">

Using this example you can import the two cards seperately (the MessageLog and the SequenceTable). However, as discussed below, the ExecutionPanel is required for the SequenceTable to work.


### Unstructured non-cards example
```js
import { useRef, useEffect, useState } from 'react';
import { useAdapterEndpoint } from 'odin-react';
import { ExecutionPanel, ModuleList, SequenceButtons } from 'odin-sequencer-react-ui';

function App() {

  const sequencer_endpoint = useAdapterEndpoint("odin_sequencer", import.meta.env.VITE_SEQUENCER_ENDPOINT_URL);

  const [sequenceModules, setSequenceModules] = useState({});
  const executionPanelRef = useRef(null);
  const [abortDisabled, setAbortDisabled] = useState(true);

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
  }, [])

  return (
    <>
      <p>
        (page loaded successfully)
      </p>
      <div className="alert-box" id="alert-container"></div>
      <ExecutionPanel endpoint={endpoint} />
      <ModuleList endpoint={endpoint} />
      <SequenceButtons endpoint={endpoint} />
    </>
  )
}

export default App

```
<img src="example/example_screenshots/unstructured.png" alt="Web page view of example above" width="700">

You are also able to import the components that make up cards as shown in the above example.

## API

### `OdinSequencer`
A fully integrated dashboard that includes all the core components.  
Use this if you want an all-in-one solution.

**Requirements**

However, you are still required to include an adapterEndpoint object, probably derived from useAdapterEndpoint.
```js
  const sequencer_endpoint = useAdapterEndpoint("odin_sequencer", import.meta.env.VITE_SEQUENCER_ENDPOINT_URL);
```

---

### `OdinSequencerMessageLog`
Displays the sequencer's message log inside a React card.  
**No setup or dependencies required.**

---

### `OdinSequencerExecutionPanel`
Contains the execution bar and an abort button. Hidden by default — becomes visible when a sequence is running.
No component relies on this via ref now, so it should be okay to be used independently, or other components without it.

**Required state/refs:**
- Sequencer endpoint

---

### `OdinSequencerModuleList`
Displays available sequence modules in a plain list/table format.

**Required state/refs:**
- Sequencer endpoint

---

### `OdinSequencerSequenceButtons`
Provides "Reload" and "Detect Changes" controls for the sequence modules.
Usually used alongside the module table.

**Requires:**
- Sequencer endpoint

---

### `OdinSequencerSequenceTable`
Combines `OdinSequencerModuleList` and `OdinSequencerSequenceButtons` into a single card UI for interacting with sequences.
Includes both the module display and control buttons.

**Requires:**
- Sequencer endpoint

---

### `sequencer_endpoint`
Provides API access methods for interacting with the backend.
Used to fetch status of sequences and information about them.

**Usage:**
```js
import { useAdapterEndpoint } from 'odin-react';

function App() {
  const sequencer_endpoint = useAdapterEndpoint("odin_sequencer", import.meta.env.VITE_SEQUENCER_ENDPOINT_URL);
  sequencer_endpoint.get('').then(...)
}
```

Best usage is with [Odin-React](https://github.com/stfc-aeg/odin-react) components instead of manual access. This removes the need to manually create and format put requests and apply onChange/etc. functions to components. This also gives consistent styling to your components.


## Compatibility

- React 18+ — Required. Minor version differences are supported, but major versions other than 18 will fail.
- Bootstrap 5 — Required for correct styling.
- React-Bootstrap — Used for layout and components.
- Build tools:
  - Tested with Vite
  - Should also work with other react build system.