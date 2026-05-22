import { create } from 'zustand'
import type { UserResponse } from '@/types'

interface AuthState {
  token: string | null
  user: UserResponse | null
  isAuthenticated: boolean
  login: (token: string, user: UserResponse) => void
  logout: () => void
  hydrate: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  login: (token: string, user: UserResponse) => {
    localStorage.setItem('sp_token', token)
    set({ token, user, isAuthenticated: true })
  },
  logout: () => {
    localStorage.removeItem('sp_token')
    set({ token: null, user: null, isAuthenticated: false })
  },
  hydrate: () => {
    const token = localStorage.getItem('sp_token')
    if (token) {
      set({ token, isAuthenticated: true })
    }
  },
}))

// Hydrate on module load
useAuthStore.getState().hydrate()
