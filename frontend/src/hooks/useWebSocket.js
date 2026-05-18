import { useEffect, useRef, useState } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useSentinelStream() {
  const [frame, setFrame] = useState(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    let alive = true
    let retryTimer

    const connect = () => {
      const ws = new WebSocket(`${WS_URL}/ws/stream`)
      wsRef.current = ws

      ws.onopen = () => {
        if (!alive) return
        setConnected(true)
        setError(null)
      }

      ws.onmessage = (ev) => {
        try {
          setFrame(JSON.parse(ev.data))
        } catch {
          /* ignore parse errors */
        }
      }

      ws.onclose = () => {
        if (!alive) return
        setConnected(false)
        retryTimer = setTimeout(connect, 2000)
      }

      ws.onerror = () => {
        setError('WebSocket connection failed')
        setConnected(false)
      }
    }

    connect()

    return () => {
      alive = false
      clearTimeout(retryTimer)
      wsRef.current?.close()
    }
  }, [])

  return { frame, connected, error }
}
