import { useRef, useImperativeHandle, forwardRef } from 'react';
import sequencer_endpoint from "../sequencerEndpoint";
import { handleAlerts } from '../alertUtils';

import './styles.css';

const ExecutionPanel = forwardRef(({ abortDisabled, setAbortDisabled }, ref) => {
    const spinnerRef = useRef(null);
    const textRef = useRef(null);
    const progressRef = useRef(null);
    const progressBarRef = useRef(null);
    const progressStatusRef = useRef(null);

    useImperativeHandle(ref, () => ({
        displayExecution: (sequenceName) => {
            if (spinnerRef.current) spinnerRef.current.classList.remove('d-none');
            if (textRef.current) textRef.current.innerHTML = `<b>Executing:&nbsp;${sequenceName}</b>`;
            if (progressBarRef.current) {
                progressBarRef.current.style.width = "0%";
                progressBarRef.current.setAttribute("aria-valuenow", 0);
            }
            if (progressStatusRef.current) progressStatusRef.current.innerHTML = "";
            if (progressRef.current) progressRef.current.classList.remove('d-none');
        },
        hideExecution: () => {
            if (progressRef.current) progressRef.current.classList.add('d-none');
            if (spinnerRef.current) spinnerRef.current.classList.add('d-none');
            if (textRef.current) textRef.current.innerHTML = "";
            if (progressStatusRef.current) progressStatusRef.current.innerHTML = "";
        },
        updateExecutionProgress: () => {
            sequencer_endpoint.get('execution_progress')
            .then(result => {
                const { current, total } = result.execution_progress;
                
                if (total !== -1) {
                    const percent = Math.floor((100 * current) / total);
                    if (progressBarRef.current) {
                        progressBarRef.current.style.width = `${percent}%`;
                        progressBarRef.current.setAttribute('aria-valuenow', percent.toString());
                    }
                    if (progressStatusRef.current) {
                        progressStatusRef.current.innerHTML = `<b>(${current}/${total})</b>`;
                    }
                } else {
                    if (progressBarRef.current) {
                        progressBarRef.current.style.width = "100%";
                    }
                    if (progressStatusRef.current) {
                        progressStatusRef.current.innerHTML = "";
                    }
                }
            })
        }
    }));
   
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
            <div className='progress-container'>
                <div className="row" style={{ marginBottom: '8px' }} >
                    <div className="d-flex flex-wrap align-items-center justify-content-between mb-2 w-100">
                        <div style={{ marginRight: '10px' }}>
                            <span ref={textRef} style={{ textAlign: 'left' }}></span>
                            <div>
                                <span ref={progressStatusRef} style={{ textAlign: 'left' }}></span>
                                <div className="spinner-border spinner-border-sm text-primary d-none" ref={spinnerRef} style={{ marginLeft: '10px' }}>
                                    <span className="visually-hidden">Executing...</span>
                                </div>
                            </div>
                        </div>
                        {!abortDisabled && (
                            <button class="btn btn-primary" onClick={abortSequence}>Abort</button>
                        )}
                    </div>

                    <div className="col-md-12">
                        <div className="progress d-none" ref={progressRef} style={{ height: '12px' }}>
                            <div
                                className="progress-bar progress-bar-striped progress-bar-animated"
                                ref={progressBarRef}
                                role="progressbar"
                                style={{ width: '0%' }}
                                aria-valuenow="0"
                                aria-valuemin="0"
                                aria-valuemax="100"
                            ></div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
});

export default ExecutionPanel;
