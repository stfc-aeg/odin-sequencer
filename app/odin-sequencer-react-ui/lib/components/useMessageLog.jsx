import sequencer_endpoint from "./sequencerEndpoint";
import { handleAlerts } from './alertUtils';

let lastMessageTimestampRef = null;

export const useMessageLog = () => {

    const getLogMessages = () => {
        const payload = lastMessageTimestampRef ? { last_message_timestamp: lastMessageTimestampRef } : {};

        return sequencer_endpoint.put(payload)
            .then(() => sequencer_endpoint.get('log_messages'));
    };

    const displayLogMessages = () => {
        getLogMessages()
        .then(result => {
            const log_messages = result.log_messages;
            if (Object.keys(log_messages).length !== 0) {

                const pre_scrollable = document.querySelector('#log-messages');
                //let lastTimestamp = lastMessageTimestampRef;

                for (const [timestampRaw, message] of log_messages) {
                    let timestamp = timestampRaw.slice(0, -3);
                    pre_scrollable.innerHTML += 
                    `<span style="color:#007bff; font-size:12px">${timestamp}</span> <span style="font-size:12px">${message}</span><br>`;
                    //lastTimestamp = timestampRaw;
                }

                // update ref to latest timestamp from the last message
                lastMessageTimestampRef = log_messages[log_messages.length - 1][0];
                pre_scrollable.scrollTop = pre_scrollable.scrollHeight;
            }
        })
        .catch(error => {
            const alert_message = 'A problem occurred while trying to get log messages: ' + error.message;
            handleAlerts({ "alert_message": alert_message, alert_type: 'danger' });
        });
    };

    return { displayLogMessages };
};

export const awaitExecutionComplete = (displayLogMessages, executionPanelRef, setAbortDisabled) => {
    sequencer_endpoint.get('is_executing')
    .then(result => {
        displayLogMessages();
        const is_executing = result.is_executing
        if (is_executing) {
            executionPanelRef.current?.updateExecutionProgress?.();
            setTimeout(() => awaitExecutionComplete(displayLogMessages, executionPanelRef, setAbortDisabled), 500);
        } else {
            // disable button toggle logic for abort TODO (true)
            setAbortDisabled(true);
            executionPanelRef.current?.hideExecution?.();
        }
    });
}

export const awaitProcessExecutionComplete = (displayLogMessages) => {
    sequencer_endpoint.get('process_tasks')
    .then(result => {
        displayLogMessages();
        const process_tasks = result.process_tasks
        if (process_tasks.length !== 0) {
            setTimeout(() => awaitProcessExecutionComplete(displayLogMessages), 500);
        }
    });
}
