import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect, vi } from 'vitest'
import DashboardPage from '../pages/DashboardPage'

// Mock the API and stores
vi.mock('../api/servers', () => ({
  list: vi.fn().mockResolvedValue([
    {
      id: 'test-1',
      name: 'Test Server',
      hostname: 'test.example.com',
      last_seen_at: new Date().toISOString(),
      status: 'online',
      created_at: new Date().toISOString(),
    },
  ]),
}))

vi.mock('../stores/authStore', () => ({
  useAuthStore: () => ({
    token: 'fake-token',
    user: { id: 'u1', email: 'test@test.com' },
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    hydrate: vi.fn(),
  }),
}))

vi.mock('../stores/serversStore', () => ({
  useServersStore: vi.fn(() => ({
    servers: [
      {
        id: 'test-1',
        name: 'Test Server',
        hostname: 'test.example.com',
        last_seen_at: new Date().toISOString(),
        status: 'online',
        created_at: new Date().toISOString(),
      },
    ],
    setServers: vi.fn(),
    addServer: vi.fn(),
    removeServer: vi.fn(),
    updateMetric: vi.fn(),
    updateStatus: vi.fn(),
  })),
}))

vi.mock('../hooks/useLiveMetrics', () => ({
  useLiveMetrics: () => ({ isConnected: false }),
}))

describe('DashboardPage', () => {
  it('renders server cards with mocked data', async () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>,
    )

    // Wait for async data to load
    const serverName = await screen.findByText('Test Server')
    expect(serverName).toBeInTheDocument()
  })
})
