import { useEffect, useRef } from 'react';
import { useMessageLog } from './useMessageLog';
import { AdapterEndpoint } from './AdapterEndpointWrapper';


const sequencer_endpoint = new AdapterEndpoint("odin_sequencer", "http://127.0.0.1:8888");

const MessageLog = () => {
    const { displayLogMessages } = useMessageLog();
    const hasLoaded = useRef(false);

    useEffect(() => {
        if (!hasLoaded.current) {
            sequencer_endpoint.put({ 'last_message_timestamp': "" })
            hasLoaded.current = true;
            displayLogMessages();
        }
    }, []);

    return (
        <>
            <h4 style={{textAlign: "center"}}>Log Messages</h4>
            <pre className="pre-scrollable" id="log-messages"></pre>
        </>
    );
};

export default MessageLog