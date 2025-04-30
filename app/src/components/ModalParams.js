import { Row } from "react-bootstrap"

/* Constructing the labels and input boxes for the parameters inside the modal. */

const ModalParams = ({sequence, inputRefs}) => {

    const paramBoxes = Object.entries(sequence).flatMap(([paramKey, param]) => {
        const paramLabel = `${String(paramKey).replaceAll(" ", "_")}-${param.type}`;

        let paramValue = param.default;
        if (paramValue != param.value) {
            paramValue = param.value;
        };

        const ref = inputRefs.current.get(paramLabel) || { current: null };
        const inputRef = (el) => {
        if (el) inputRefs.current.set(paramLabel, el);
        };

        const paramName = `${String(paramKey).replaceAll(" ", "_")} (${param.type})`;
        return (
        <>
            <Row key={paramLabel} style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ width: '160px' }}>{paramName}</span>
                <span style={{ flex: 1 }}>
                    <label>
                    <input
                        style={{ width: '280px' }}
                        name={paramLabel}
                        defaultValue={paramValue}
                        ref={inputRef}
                    />
                    </label>
                </span>
            </Row>
        </>
        )
    })
    return paramBoxes
}

export default ModalParams