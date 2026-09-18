import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { toast } from 'sonner'
import { apiFetch, ApiError } from '@/api/client'
import { getAccessToken, setTokens } from '@/lib/token-storage'

vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('apiFetch', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.mocked(toast.error).mockClear()
    vi.stubGlobal('fetch', vi.fn())
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, assign: vi.fn() },
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('attaches the stored access token as a Bearer header', async () => {
    setTokens('access-1', 'refresh-1')
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { ok: true }))

    await apiFetch('/candidates/cv')

    const [, init] = vi.mocked(fetch).mock.calls[0]
    expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer access-1')
  })

  it('on 401, refreshes the token and retries the original request once', async () => {
    setTokens('expired', 'refresh-1')
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Invalid or expired token' }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: 'fresh', refresh_token: 'refresh-2' }))
      .mockResolvedValueOnce(jsonResponse(200, { data: 'ok' }))

    const response = await apiFetch('/candidates/cv')

    expect(response.status).toBe(200)
    expect(getAccessToken()).toBe('fresh')
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(3)
    expect(vi.mocked(fetch).mock.calls[1][0]).toContain('/auth/refresh')

    const retryInit = vi.mocked(fetch).mock.calls[2][1]
    expect((retryInit?.headers as Record<string, string>).Authorization).toBe('Bearer fresh')
  })

  it('deduplicates concurrent refresh calls into a single /auth/refresh request', async () => {
    setTokens('expired', 'refresh-1')

    vi.mocked(fetch).mockImplementation((url, init) => {
      const path = String(url)
      const authHeader = (init?.headers as Record<string, string> | undefined)?.Authorization

      if (path.includes('/auth/refresh')) {
        return Promise.resolve(jsonResponse(200, { access_token: 'fresh', refresh_token: 'refresh-2' }))
      }
      if (authHeader === 'Bearer expired') {
        return Promise.resolve(jsonResponse(401, { detail: 'Invalid or expired token' }))
      }
      return Promise.resolve(jsonResponse(200, { ok: true }))
    })

    const [resA, resB] = await Promise.all([apiFetch('/a'), apiFetch('/b')])

    expect(resA.status).toBe(200)
    expect(resB.status).toBe(200)

    const refreshCalls = vi.mocked(fetch).mock.calls.filter(([url]) => String(url).includes('/auth/refresh'))
    expect(refreshCalls).toHaveLength(1)
  })

  it('clears tokens and redirects to /login when the refresh call itself fails', async () => {
    setTokens('expired', 'refresh-1')
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Invalid or expired token' }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Invalid refresh token' }))

    await expect(apiFetch('/candidates/cv')).rejects.toThrow(ApiError)

    expect(getAccessToken()).toBeNull()
    expect(window.location.assign).toHaveBeenCalledWith('/login')
  })

  it('shows a rate-limit toast on a 429 response', async () => {
    setTokens('access-1', 'refresh-1')
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(429, { detail: 'Too Many Requests' }))

    await expect(apiFetch('/candidates/cv')).rejects.toThrow(ApiError)

    expect(toast.error).toHaveBeenCalledWith(
      'Забагато запитів. Зачекайте трохи і спробуйте ще раз.',
      { id: 'rate-limit' },
    )
  })
})
