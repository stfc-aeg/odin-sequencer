import { useEffect, useRef, useState } from 'react'
import { TitleCard, WithEndpoint } from 'odin-react'
import { Form, Col } from 'react-bootstrap'

const POLL_INTERVAL_MS = 1000
const EndpointFormControl = WithEndpoint(Form.Control);

const MessageLog = ({ endpoint }) => {
  const [messages, setMessages] = useState([])
  const lastTimestampRef = useRef(null)

  useEffect(() => {
    let timer

    const fetchLogs = async () => {
      const params = lastTimestampRef.current
        ? { last_message_timestamp: lastTimestampRef.current }
        : undefined

      const response = await endpoint.get('log_messages', params)
      const newLogs = response?.log_messages ?? []

      if (!newLogs.length) return

      setMessages(prev => {
        // Filter out anything we've already seen (safety net)
        const filtered = newLogs.filter(
          ([ts, msg]) =>
            !prev.some(([pTs, pMsg]) => pTs === ts && pMsg === msg)
        )

        if (!filtered.length) return prev

        const last = filtered.at(-1)
        lastTimestampRef.current = last[0]

        return [...prev, ...filtered]
      })
    }

    fetchLogs()
    timer = setInterval(fetchLogs, POLL_INTERVAL_MS)

    return () => clearInterval(timer)
  }, [endpoint])

  const logText = messages
    .map(([timestamp, msg]) => `[${timestamp}] ${msg}`)
    .join('\n')

  return (
    <TitleCard title="Log Messages">
      <Col>
        <EndpointFormControl
          endpoint={endpoint}
          fullpath="log_messages"
          as="textarea"
          readOnly
          disabled
          value={logText}
          style={{
            height: '600px',
            overflowY: 'auto',
            resize: 'none',
            whiteSpace: 'pre-wrap',
            fontFamily: 'monospace',
            backgroundColor: '#f7f7f7'
          }}
        />
      </Col>
    </TitleCard>
  )


  // return (
  //   <TitleCard title="Log Messages">
  //     <Col>
  //       <Form.Control
  //         as="textarea"
  //         readOnly
  //         value={logText}
  //         style={{
  //           height: '600px',
  //           overflowY: 'auto',
  //           resize: 'none',
  //           whiteSpace: 'pre-wrap',
  //           fontFamily: 'monospace',
  //           backgroundColor: '#f7f7f7'
  //         }}
  //       />
  //     </Col>
  //   </TitleCard>
  // )
}

export default MessageLog