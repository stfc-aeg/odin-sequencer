import { useEffect, useRef, useState, useCallback } from 'react'
import { OdinEventLog } from 'odin-react'

const POLL_INTERVAL_MS = 1000

const MessageLog = ({ endpoint }) => {
  const [events, setEvents] = useState([])
  const lastTimestampRef = useRef(null)

  const getLatestLogs = useCallback((timestamp) => {
    return events.filter(event => 
      !timestamp || new Date(event.timestamp) > new Date(timestamp)
    )
  }, [events])

  useEffect(() => {
    let timer

    const fetchLogs = async () => {
      const params = lastTimestampRef.current
        ? { last_message_timestamp: lastTimestampRef.current }
        : undefined

      const response = await endpoint.get('log_messages', params)
      const newLogs = response?.log_messages ?? []

      if (!newLogs.length) return

      setEvents(prev => {
        const transformed = newLogs.map(([timestamp, message, level]) => ({
          timestamp,
          message,
          level
        }))

        const filtered = transformed.filter(
          (log) =>
            !prev.some(
              (pLog) => pLog.timestamp === log.timestamp && pLog.message === log.message
            )
        )

        if (!filtered.length) return prev

        const last = filtered.at(-1)
        lastTimestampRef.current = last.timestamp

        return [...prev, ...filtered]
      })
    }

    fetchLogs()
    timer = setInterval(fetchLogs, POLL_INTERVAL_MS)

    return () => clearInterval(timer)
  }, [endpoint])

  return (
    <OdinEventLog
      events={events}
      getLatestLogs={getLatestLogs}
      refreshRate={POLL_INTERVAL_MS}
      displayHeight="500px"
    />
  )
}

export default MessageLog