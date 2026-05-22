import { api } from './client'
import type { TokenResponse, UserResponse } from '@/types'

export async function login(email: string, password: string): Promise<TokenResponse> {
  return api<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function register(email: string, password: string): Promise<UserResponse> {
  return api<UserResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function me(): Promise<UserResponse> {
  return api<UserResponse>('/api/v1/auth/me')
}
