import { api } from './client'
import type { ServerResponse, ServerWithToken, MetricResponse } from '@/types'

export async function list(): Promise<ServerResponse[]> {
  return api<ServerResponse[]>('/api/v1/servers/')
}

export async function get(id: string): Promise<ServerResponse> {
  return api<ServerResponse>(`/api/v1/servers/${id}`)
}

export async function create(name: string, hostname: string): Promise<ServerWithToken> {
  return api<ServerWithToken>('/api/v1/servers/', {
    method: 'POST',
    body: JSON.stringify({ name, hostname }),
  })
}

export async function remove(id: string): Promise<void> {
  return api<void>(`/api/v1/servers/${id}`, { method: 'DELETE' })
}

export async function regenerateToken(id: string): Promise<ServerWithToken> {
  return api<ServerWithToken>(`/api/v1/servers/${id}/regenerate-token`, {
    method: 'POST',
  })
}

export async function queryMetrics(
  serverId: string,
  from: string,
  to: string,
): Promise<MetricResponse[]> {
  const params = new URLSearchParams({ from, to })
  return api<MetricResponse[]>(`/api/v1/servers/${serverId}/metrics?${params}`)
}
