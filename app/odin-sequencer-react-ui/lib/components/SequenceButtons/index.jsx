import { useState, useEffect, useRef } from 'react';
import { useMessageLog } from '../useMessageLog';
import { handleAlerts } from '../alertUtils';
import { awaitExecutionComplete, awaitProcessExecutionComplete } from '../useMessageLog';

import './styles.css';

const SequenceButtons = ({ reloadModules, executionPanelRef, setAbortDisabled, sequencer_endpoint }) => {
    const { displayLogMessages } = useMessageLog({ sequencer_endpoint });
    const hasLoaded = useRef(false);
    const [detectChanges, setDetectChanges] = useState(false);
    const pollingRef = useRef(false);

    const setAbort = (checked) => {
        setAbortDisabled(checked);
    }

    useEffect(() => {
        if (!hasLoaded.current) {
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
                    // disable button toggle logic for abort TODO (false)
                    setAbort(false);
                    executionPanelRef.current?.displayExecution(result.execute);
                    awaitExecutionComplete(displayLogMessages, executionPanelRef, setAbortDisabled, sequencer_endpoint);
                    awaitProcessExecutionComplete(displayLogMessages, sequencer_endpoint);
                }
                else
                {
                    // disable button toggle logic for abort TODO (true)
                    setAbort(true);
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

    return (
        <>
            <div className="button-row">
                <div className="form-switch d-flex align-items-center mb-0">
                    <input
                        className="form-check-input"
                        type="checkbox"
                        id="detect-module-changes-toggle"
                        checked={detectChanges}
                        onChange={e => toggleDetectChanges(e.target.checked)}
                    />
                    <label className="form-check-label" htmlFor="detect-module-changes-toggle"><span style={{ marginLeft: '8px', fontWeight: 500, fontSize: '1rem' }}>Detect&nbsp;Changes</span></label>
                </div>
                <button className="btn btn-primary" onClick={handleReloadClick}>Reload</button>
            </div>
        </>
    );
};

export default SequenceButtons
