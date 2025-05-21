import { AdapterEndpoint } from './AdapterEndpointWrapper';

const ENDPOINT_URL = "http://127.0.0.1:8888";
const sequencer_endpoint = new AdapterEndpoint("odin_sequencer", ENDPOINT_URL);

export default sequencer_endpoint;
