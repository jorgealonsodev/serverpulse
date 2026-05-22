export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
}

export interface ServerResponse {
  id: string
  name: string
  hostname: string | null
  last_seen_at: string | null
  status: 'online' | 'offline'
  created_at: string
}

export interface ServerWithToken extends ServerResponse {
  api_token: string
}

export interface MetricResponse {
  id: number
  server_id: string
  cpu_percent: number
  ram_percent: number
  ram_used_mb: number
  ram_total_mb: number
  disk_percent: number
  disk_used_gb: number
  disk_total_gb: number
  net_rx_bytes: number
  net_tx_bytes: number
  uptime_seconds: number
  load_avg_1: number | null
  load_avg_5: number | null
  load_avg_15: number | null
  recorded_at: string
  received_at: string
}

export interface WsMessage {
  type: 'metric' | 'status_change'
  server_id: string
  data?: MetricResponse
  status?: 'online' | 'offline'
}

export type TimeRange = '1h' | '6h' | '24h'
