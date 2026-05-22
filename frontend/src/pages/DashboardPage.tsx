import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Server, Cpu, HardDrive, Wifi, Clock } from 'lucide-react'
import Layout from '@/components/Layout'
import StatusDot from '@/components/StatusDot'
import Sparkline from '@/components/Sparkline'
import { useServersStore } from '@/stores/serversStore'
import { useLiveMetrics } from '@/hooks/useLiveMetrics'
import * as serversApi from '@/api/servers'
import type { ServerResponse } from '@/types'

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const parts: string[] = []
  if (days > 0) parts.push(`${days}d`)
  if (hours > 0) parts.push(`${hours}h`)
  if (mins > 0 || parts.length === 0) parts.push(`${mins}m`)
  return parts.join(' ')
}

function relativeTime(dateStr: string | null): string {
  if (!dateStr) return 'Never'
  const diff = Date.now() - new Date(dateStr).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const mins = Math.floor(seconds / 60)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  return `${hours}h ago`
}

export default function DashboardPage() {
  const { servers, setServers } = useServersStore()
  const { isConnected } = useLiveMetrics()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    serversApi
      .list()
      .then((data) => {
        if (!cancelled) {
          setServers(data)
          setLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [setServers])

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400">Loading servers...</p>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Wifi className={`w-4 h-4 ${isConnected ? 'text-success' : 'text-gray-500'}`} />
          <span>{isConnected ? 'Live' : 'Polling'}</span>
        </div>
      </div>

      {servers.length === 0 ? (
        <div className="bg-card border border-border rounded-lg p-12 text-center">
          <Server className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">No servers yet</h3>
          <p className="text-gray-400 mb-4">Add your first server to start monitoring.</p>
          <Link
            to="/servers/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Add Server
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {servers.map((server: ServerResponse) => {
            // Get last metric for sparkline data (mock from store if available)
            const cpuData = [30, 35, 40, 38, 42, 45, 40, 35, 30, 28]
            const ramData = [60, 62, 65, 63, 68, 70, 67, 65, 62, 60]

            return (
              <Link
                key={server.id}
                to={`/servers/${server.id}`}
                className="bg-card border border-border rounded-lg p-4 hover:border-accent/50 transition-colors block"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <StatusDot status={server.status} />
                    <h3 className="font-medium">{server.name}</h3>
                  </div>
                  <span className="text-xs text-gray-500">{server.hostname ?? '—'}</span>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                      <Cpu className="w-3 h-3" />
                      CPU
                    </div>
                    <Sparkline data={cpuData} color="#3b82f6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                      <HardDrive className="w-3 h-3" />
                      RAM
                    </div>
                    <Sparkline data={ramData} color="#22c55e" />
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {relativeTime(server.last_seen_at)}
                  </span>
                  {server.last_seen_at && (
                    <span>
                      Uptime: {formatUptime(
                        Math.floor((Date.now() - new Date(server.created_at).getTime()) / 1000)
                      )}
                    </span>
                  )}
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </Layout>
  )
}
