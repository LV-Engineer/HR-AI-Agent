import { toast } from 'sonner'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/lib/token-storage'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

function buildHeaders(init: RequestInit | undefined, token: string | null): HeadersInit {
  const isFormData = init?.body instanceof FormData
  return {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...init?.headers,
  }
}

async function rawFetch(path: string, init: RequestInit | undefined, token: string | null): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, { ...init, headers: buildHeaders(init, token) })
}

let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refreshToken = getRefreshToken()
      if (!refreshToken) throw new Error('No refresh token')

      const response = await rawFetch(
        '/auth/refresh',
        { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) },
        null,
      )
      if (!response.ok) throw new Error('Refresh failed')

      const tokens: { access_token: string; refresh_token: string } = await response.json()
      setTokens(tokens.access_token, tokens.refresh_token)
      return tokens.access_token
    })().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

async function toApiResult(response: Response): Promise<Response> {
  if (response.status === 429) {
    toast.error('Забагато запитів. Зачекайте трохи і спробуйте ще раз.', { id: 'rate-limit' })
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(response.status, body?.detail ?? 'Помилка запиту')
  }
  return response
}

const AUTH_PATHS = ['/auth/login', '/auth/refresh']

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const response = await rawFetch(path, init, getAccessToken())

  if (response.status === 401 && !AUTH_PATHS.includes(path)) {
    try {
      const newAccessToken = await refreshAccessToken()
      return toApiResult(await rawFetch(path, init, newAccessToken))
    } catch {
      clearTokens()
      window.location.assign('/login')
      throw new ApiError(401, 'Сесія завершилась')
    }
  }

  return toApiResult(response)
}
