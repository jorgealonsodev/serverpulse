const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

interface RequestOptions extends RequestInit {
  skipAuth?: boolean
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { skipAuth, headers, ...rest } = options

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (headers) {
    for (const [key, value] of Object.entries(headers)) {
      if (typeof value === 'string') {
        requestHeaders[key] = value
      }
    }
  }

  if (!skipAuth) {
    const token = localStorage.getItem('sp_token')
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`
    }
  }

  const url = path.startsWith('http') ? path : `${API_BASE}${path}`

  const response = await fetch(url, {
    ...rest,
    headers: requestHeaders,
  })

  if (response.status === 401 && !skipAuth) {
    localStorage.removeItem('sp_token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      // ignore
    }
    throw new Error(detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}
