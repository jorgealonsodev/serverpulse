import { useEffect, useRef, useState, useCallback } from 'react'
import { useServersStore } from '@/stores/serversStore'
import type { WsMessage, MetricResponse } from '@/types'
import * as serversApi from '@/api/servers'

const POLL_INTERVAL_MS = 15_000

export function useLiveMetrics() {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const { updateMetric, updateStatus, servers } = useServersStore()

  const pollAll = useCallback(async () => {
    for (const server of servers) {
      try {
        const now = new Date()
        const from = new Date(now.getTime() - 60 * 60 * 1000) // 1h window
        const metrics = await serversApi.queryMetrics(
          server.id,
          from.toISOString(),
          now.toISOString(),
        )
        if (metrics.length > 0) {
          const latest = metrics[metrics.length - 1]
          updateMetric(server.id, latest)
        }
      } catch {
        // ignore polling errors
      }
    }
  }, [servers, updateMetric])

  useEffect(() => {
    const token = localStorage.getItem('sp_token')
    if (!token) return

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws?token=${token}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      wsRef.current = null
      // Start polling fallback
      pollRef.current = setInterval(pollAll, POLL_INTERVAL_MS)
    }

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        if (msg.type === 'metric' && msg.data) {
          updateMetric(msg.server_id, msg.data as MetricResponse)
        } else if (msg.type === 'status_change' && msg.status) {
          updateStatus(msg.server_id, msg.status)
        }
      } catch {
        // ignore parse errors
      }
    }

    return () => {
      ws.close()
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [updateMetric, updateStatus, pollAll])

  return { isConnected }
}
