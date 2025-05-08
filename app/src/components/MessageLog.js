import { useEffect, useRef } from 'react';
import { useMessageLog } from './useMessageLog';
import { AdapterEndpoint } from './AdapterEndpointWrapper';
import { handleAlerts } from './alertUtils';

const execution_spinner = document.getElementById("execution-status-spinner");
const execution_text = document.getElementById("execution-status-text");
const execution_progress = document.getElementById("execution-progress");
const execution_progress_bar = document.getElementById("execution-progress-bar");
const execution_status_progress = document.getElementById("execution-status-progress");

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

    const handleOpenModal = () => {

    };

    return (
        <>
            <h4 style={{textAlign: "center"}}>Log Messages</h4>
            <pre className="pre-scrollable" id="log-messages"></pre>


            <div class="button-row">
                <button onClick={handleOpenModal}>Abort</button>
                <div class="center-text form-switch">
                    <input class="form-check-input" type="checkbox" id="detect-module-changes-toggle"></input>
                    <label class="form-check-label" for="detect-module-changes-toggle"><b>Detect&nbsp;Changes</b></label>
                </div>
                <button onClick={handleOpenModal}>Reload</button>
            </div>

            <div className="row">
                <div className="col-md-12">
                    <div
                        className="spinner-border spinner-border-sm text-primary d-none"
                        role="status"
                        id="execution-status-spinner"
                    >
                        <span className="visually-hidden">Executing...</span>
                    </div>
                    <span id="execution-status-text" style={{ textAlign: 'left' }}></span>
                    <span id="execution-status-progress" style={{ textAlign: 'left' }}></span>
                </div>
            </div>

            <div className="row">
                <div className="col-md-12">
                    <div
                        className="progress d-none"
                        id="execution-progress"
                        style={{ height: '12px' }}
                    >
                        <div
                            className="progress-bar progress-bar-striped progress-bar-animated"
                            id="execution-progress-bar"
                            role="progressbar"
                            style={{ width: '0%' }}
                            aria-valuenow="0"
                            aria-valuemin="0"
                            aria-valuemax="100"
                        ></div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default MessageLog





// /*
//  * This function displays the excution progress elements on the UI
//  */
// function display_execution(sequence_name)
// {
//     execution_spinner.classList.remove('d-none');
//     execution_text.innerHTML = "<b>Executing:&nbsp;" + sequence_name + "</b>";
//     execution_progress_bar.style.width = "0%";
//     execution_progress_bar.setAttribute('aria-valuenow', 0);
//     execution_status_progress.innerHTML = ""

//     execution_progress.classList.remove('d-none');
// }

// /*
//  * This function hides the excution progress elements on the UI
//  */
// function hide_execution()
// {
//     execution_progress.classList.add('d-none');
//     execution_spinner.classList.add('d-none');
//     execution_text.innerHTML = "";
//     execution_status_progress.innerHTML = "";
// }

// /*
//  * This function updates the execution progress bar
//  */

// function update_execution_progress()
// {
//     sequencer_endpoint.get('execution_progress')
//     .then(result => {
//         var current = result.execution_progress.current;
//         var total = result.execution_progress.total;
//         if (total != -1)
//         {
//             var percent_complete = Math.floor((100.0 * current) / total);
//             execution_progress_bar.style.width = percent_complete + "%";
//             execution_progress_bar.setAttribute('aria-valuenow', percent_complete);
//             execution_status_progress.innerHTML = "<b>(" + current + "/" + total + ")</b>";
//         }
//         else
//         {
//             execution_progress_bar.style.width = "100%";
//             execution_status_progress.innerHTML = "";
//         }
//     });
// }

// /**
//  * This function listens for module changes by calling itself every second. It displays
//  * an alert message when it detects that the backend has reported of module changes. 
//  */
// function await_module_changes() {
//     sequencer_endpoint.get('module_modifications_detected')
//     .then(result => {
//         if (result.module_modifications_detected) {
//             info_message = 'Code changes were detected, click the Reload button to load them';
//             display_alert(ALERT_ID['sequencer_info'], info_message);
//         }

//         if (detect_module_modifications) {
//             setTimeout(await_module_changes, 1000);
//         }
//     })
//     .catch(error => {
//         display_alert(ALERT_ID['sequencer_error'], error.message);
//     });
// }

// /**
//  * This function enables or disables the Detect Changes toggle.
//  */
// function set_detect_module_changes_toggle(detect_module_modifications) {
//     detect_changes_switch.checked = detect_module_modifications;
// }

// /**
//  * This function calls the reloading mechanism implemented on the backend which decides
//  * which modules need to be reloaded. It disables the execute and reload buttons before
//  * making a call to the backend and enables them when the process completes or fails.
//  * It also calls the build_sequence_modules_layout to rebuild the layout and displays
//  * the relevant messages in the alerts depending on the process outcome.
//  */
// function reload_modules() {
//     hide_alerts(`${ALERT_ID['sequencer_info']},${ALERT_ID['sequencer_error']}`);
//     disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true);

//     alert_id = '';
//     alert_message = '';
//     sequencer_endpoint.put({ 'reload': true })
//     .then(() => {
//         alert_id = ALERT_ID['sequencer_info'];
//         alert_message = 'The sequence modules were successfully reloaded';
//     })
//     .catch(error => {
//         alert_id = ALERT_ID['sequencer_error'];
//         alert_message = error.message
//         if (!alert_message.startsWith('Cannot start the reloading')) {
//             alert_message += '.<br><br>To load the missing sequences, first resolve the errors and then click the Reload button.';
//         }
//     })
//     .then(() => {
//         display_alert(alert_id, alert_message);
//         build_sequence_modules_layout();
//         disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, false);
//     });
// }

function abort_sequence() {
    //hide_alerts(`${ALERT_ID['sequencer_info']},${ALERT_ID['sequencer_error']}`);

    sequencer_endpoint.put({ 'abort': true })
    .then(() => {
        const alert = {
            alert_message: "Abort sent to currently executing sequence",
            alert_type: "primary"
        };
    })
    .catch(error => {
        const alert = {
            alert_message: error.message,
            alert_type: "danger"
        };
    })
    .then(() => {
        handleAlerts(alert);
    });
}