import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Trash2, RefreshCw } from 'lucide-react'
import Layout from '@/components/Layout'
import MetricChart from '@/components/MetricChart'
import TimeRangeSelector from '@/components/TimeRangeSelector'
import ConfirmModal from '@/components/ConfirmModal'
import CopyButton from '@/components/CopyButton'
import * as serversApi from '@/api/servers'
import type { MetricResponse, ServerResponse, TimeRange, ServerWithToken } from '@/types'

export default function ServerDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [server, setServer] = useState<ServerResponse | null>(null)
  const [metrics, setMetrics] = useState<MetricResponse[]>([])
  const [range, setRange] = useState<TimeRange>('1h')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showDelete, setShowDelete] = useState(false)
  const [regeneratedToken, setRegeneratedToken] = useState<ServerWithToken | null>(null)

  const fetchMetrics = useCallback(async () => {
    if (!id) return
    const now = new Date()
    const hours = range === '1h' ? 1 : range === '6h' ? 6 : 24
    const from = new Date(now.getTime() - hours * 60 * 60 * 1000)

    try {
      const data = await serversApi.queryMetrics(id, from.toISOString(), now.toISOString())
      setMetrics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
    }
  }, [id, range])

  useEffect(() => {
    if (!id) return
    let cancelled = false

    serversApi
      .get(id)
      .then((data) => {
        if (!cancelled) {
          setServer(data)
          setLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [id])

  useEffect(() => {
    fetchMetrics()
  }, [fetchMetrics])

  const handleRegenerateToken = async () => {
    if (!id) return
    try {
      const result = await serversApi.regenerateToken(id)
      setRegeneratedToken(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate token')
    }
  }

  const handleDelete = async () => {
    if (!id) return
    try {
      await serversApi.remove(id)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete server')
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400">Loading server details...</p>
        </div>
      </Layout>
    )
  }

  if (!server) {
    return (
      <Layout>
        <div className="text-center text-gray-400">Server not found</div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">{server.name}</h2>
            {server.hostname && (
              <p className="text-sm text-gray-400">{server.hostname}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRegenerateToken}
              className="inline-flex items-center gap-1 px-3 py-2 text-sm bg-border text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Regenerate Token
            </button>
            <button
              onClick={() => setShowDelete(true)}
              className="inline-flex items-center gap-1 px-3 py-2 text-sm bg-danger/10 text-danger border border-danger/30 rounded-lg hover:bg-danger/20 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-danger/10 border border-danger/30 text-danger text-sm rounded-lg">
          {error}
        </div>
      )}

      {regeneratedToken && (
        <div className="bg-card border border-border rounded-lg p-4 mb-6">
          <h3 className="text-sm font-medium text-gray-300 mb-2">
            New API Token (save it now — shown only once)
          </h3>
          <div className="flex items-center gap-2">
            <code className="flex-1 px-3 py-2 bg-bg border border-border rounded-lg text-sm font-mono break-all">
              {regeneratedToken.api_token}
            </code>
            <CopyButton text={regeneratedToken.api_token} />
          </div>
        </div>
      )}

      <div className="mb-4">
        <TimeRangeSelector value={range} onChange={setRange} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <MetricChart
          data={metrics}
          dataKey="cpu_percent"
          color="#3b82f6"
          title="CPU %"
        />
        <MetricChart
          data={metrics}
          dataKey="ram_percent"
          color="#22c55e"
          title="RAM %"
        />
        <MetricChart
          data={metrics}
          dataKey="disk_percent"
          color="#f59e0b"
          title="Disk %"
        />
        <MetricChart
          data={metrics}
          dataKey="net_rx_bytes"
          color="#a855f7"
          title="Net RX (bytes)"
          unit=" B"
        />
      </div>

      {showDelete && (
        <ConfirmModal
          title="Delete Server"
          message={`Are you sure you want to delete "${server.name}"? This action cannot be undone.`}
          onConfirm={handleDelete}
          onCancel={() => setShowDelete(false)}
        />
      )}
    </Layout>
  )
}
