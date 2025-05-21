import './styles.css';

const MessageLog = () => {
    return (
        <>
            <div className="ui-card">
                <div className="ui-card-header">Log Messages</div>
                <div className="ui-card-body message-box">
                    <pre className="pre-scrollable" id="log-messages"></pre>
                </div>
            </div>
        </>
    )
}

export default MessageLog
