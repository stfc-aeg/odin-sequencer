import { useState, useEffect, useRef } from 'react';
import { useMessageLog } from './useMessageLog';
import { AdapterEndpoint } from './AdapterEndpointWrapper';
import { handleAlerts } from './alertUtils';
import { awaitExecutionComplete, awaitProcessExecutionComplete } from './useMessageLog';

const sequencer_endpoint = new AdapterEndpoint("odin_sequencer", "http://127.0.0.1:8888");

const MessageLog = ({ reloadModules, executionPanelRef }) => {
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
            
            sequencer_endpoint.get('')
            .then(result => {
                const is_executing = result.is_executing;

                if (is_executing) {
                    executionPanelRef.current?.displayExecution(result.execute);
                    awaitExecutionComplete(displayLogMessages, executionPanelRef);
                    awaitProcessExecutionComplete(displayLogMessages);
                }
                else
                {
                    executionPanelRef.current?.hideExecution();
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
        </>
    );
};

export default MessageLog
