import { create } from 'zustand'
import type { ServerResponse, MetricResponse } from '@/types'

interface ServersState {
  servers: ServerResponse[]
  setServers: (servers: ServerResponse[]) => void
  addServer: (server: ServerResponse) => void
  removeServer: (id: string) => void
  updateMetric: (serverId: string, metric: MetricResponse) => void
  updateStatus: (serverId: string, status: 'online' | 'offline') => void
}

export const useServersStore = create<ServersState>((set) => ({
  servers: [],
  setServers: (servers) => set({ servers }),
  addServer: (server) => set((state) => ({ servers: [...state.servers, server] })),
  removeServer: (id) => set((state) => ({ servers: state.servers.filter((s) => s.id !== id) })),
  updateMetric: (serverId, metric) =>
    set((state) => ({
      servers: state.servers.map((s) =>
        s.id === serverId
          ? { ...s, last_seen_at: metric.recorded_at, status: 'online' }
          : s,
      ),
    })),
  updateStatus: (serverId, status) =>
    set((state) => ({
      servers: state.servers.map((s) =>
        s.id === serverId ? { ...s, status } : s,
      ),
    })),
}))
