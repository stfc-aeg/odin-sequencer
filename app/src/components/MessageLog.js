import { useState, useEffect, useRef } from 'react';
import { useMessageLog } from './useMessageLog';
import { AdapterEndpoint } from './AdapterEndpointWrapper';
import { handleAlerts } from './alertUtils';

const execution_spinner = document.getElementById("execution-status-spinner");
const execution_text = document.getElementById("execution-status-text");
const execution_progress = document.getElementById("execution-progress");
const execution_progress_bar = document.getElementById("execution-progress-bar");
const execution_status_progress = document.getElementById("execution-status-progress");

const sequencer_endpoint = new AdapterEndpoint("odin_sequencer", "http://127.0.0.1:8888");

const MessageLog = ({ reloadModules }) => {
    const { displayLogMessages } = useMessageLog();
    const hasLoaded = useRef(false);
    const [detectChanges, setDetectChanges] = useState(false);
    const pollingRef = useRef(false);

    useEffect(() => {
        if (!hasLoaded.current) {
            sequencer_endpoint.put({ 'last_message_timestamp': "" });
            hasLoaded.current = true;
            displayLogMessages();
    
            // Check if detect_module_modifications is already enabled
            sequencer_endpoint.get('detect_module_modifications')
                .then(result => {
                    if (result.detect_module_modifications) {
                        setDetectChanges(true);
                        pollingRef.current = true;
                        awaitModuleChanges();
                    }
                })
                .catch(error => {
                    handleAlerts({ alert_message: error.message, alert_type: 'danger' });
                });
        }
    }, []);

    const awaitModuleChanges = () => {
        if (!pollingRef.current) return;
    
        sequencer_endpoint.get('module_modifications_detected')
            .then(result => {
                if (result.module_modifications_detected) {
                    const info_message = 'Code changes were detected, click the Reload button to load them';
                    handleAlerts({ alert_message: info_message, alert_type: 'info' });
                }
            })
            .catch(error => {
                handleAlerts({ alert_message: error.message, alert_type: 'danger' });
            })
            .finally(() => {
                if (pollingRef.current) {
                    setTimeout(awaitModuleChanges, 1000);
                }
            });
    };

    const toggleDetectChanges = (enabled) => {
        sequencer_endpoint.put({ 'detect_module_modifications': enabled })
            .then(() => {
                setDetectChanges(enabled);
                pollingRef.current = enabled;
                if (enabled) {
                    awaitModuleChanges();
                }
            })
            .catch(error => {
                handleAlerts({ alert_message: error.message, alert_type: 'danger' });
                setDetectChanges(false);
                pollingRef.current = false;
            });
    };

    /**
     * This function calls the reloading mechanism implemented on the backend which decides
     * which modules need to be reloaded. It disables the execute and reload buttons before
     * making a call to the backend and enables them when the process completes or fails.
     * It also calls the build_sequence_modules_layout to rebuild the layout and displays
     * the relevant messages in the alerts depending on the process outcome.
     */
    const handleReloadClick = () => {
        //disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true); TODO
    
        let alert_message = '';
        let alert_type = '';
        sequencer_endpoint.put({ 'reload': true })
        .then(() => {
            alert_type = "primary";
            alert_message = 'The sequence modules were successfully reloaded';
            return reloadModules();
        })
        .catch(error => {
            alert_type = "danger";
            alert_message = error.message
            if (!alert_message.startsWith('Cannot start the reloading')) {
                alert_message += '.<br><br>To load the missing sequences, first resolve the errors and then click the Reload button.';
            }
        })
        .then(() => {
            const alert = {
                alert_message: alert_message,
                alert_type: alert_type
            };
            handleAlerts(alert);
            //disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, false); TODO
        });
    };

    const abortSequence = () => {
        let alert_message = "";
        let alert_type = "";
    
        sequencer_endpoint.put({ 'abort': true })
        .then(() => {
            alert_message = "Abort sent to currently executing sequence";
            alert_type = "primary";
        })
        .catch(error => {
            alert_message = error.message;
            alert_type = "danger";
        })
        .then(() => {
            const alert = {
                alert_message: alert_message,
                alert_type: alert_type
            };
            handleAlerts(alert);
        });
    }

    return (
        <>
            <h4 style={{textAlign: "center"}}>Log Messages</h4>
            <pre className="pre-scrollable" id="log-messages"></pre>


            <div class="button-row">
                <button class="btn btn-primary" onClick={abortSequence}>Abort</button>
                <div className="center-text form-switch">
                    <input
                        className="form-check-input"
                        type="checkbox"
                        id="detect-module-changes-toggle"
                        checked={detectChanges}
                        onChange={e => toggleDetectChanges(e.target.checked)}
                    />
                    <label className="form-check-label" htmlFor="detect-module-changes-toggle"><b style={{ marginLeft: '8px' }}>Detect&nbsp;Changes</b></label>
                </div>
                <button className="btn btn-primary" onClick={handleReloadClick}>Reload</button>
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
