import { useRef, useImperativeHandle, forwardRef } from 'react';
import { AdapterEndpoint } from './AdapterEndpointWrapper';

const sequencer_endpoint = new AdapterEndpoint("odin_sequencer", "http://127.0.0.1:8888");

const ExecutionPanel = forwardRef((props, ref) => {
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

    return (
        <>
            <div className="row">
                <div className="col-md-12">
                    <div className="spinner-border spinner-border-sm text-primary d-none" ref={spinnerRef} style={{ marginRight: '10px' }}>
                        <span className="visually-hidden">Executing...</span>
                    </div>
                    <span ref={textRef} style={{ textAlign: 'left' }}></span>
                    <span ref={progressStatusRef} style={{ textAlign: 'left' }}></span>
                </div>
            </div>

            <div className="row" style={{ marginBottom: '8px' }} >
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
        </>
    );
});

export default ExecutionPanel;
