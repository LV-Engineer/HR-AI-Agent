import { describe, expect, it, vi, beforeEach } from 'vitest'
import { login, getMe } from '@/api/auth'
import { apiFetch } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiFetch: vi.fn(),
}))

function mockResponse(body: unknown) {
  return { json: () => Promise.resolve(body) } as Response
}

describe('api/auth', () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset()
  })

  it('login POSTs email and password as JSON to /auth/login', async () => {
    vi.mocked(apiFetch).mockResolvedValue(
      mockResponse({ access_token: 'a', refresh_token: 'r', token_type: 'bearer' }),
    )

    await login('oksana.kravets@hirelume.dev', 'secret')

    const [path, init] = vi.mocked(apiFetch).mock.calls[0]
    expect(path).toBe('/auth/login')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({
      email: 'oksana.kravets@hirelume.dev',
      password: 'secret',
    })
  })

  it('getMe GETs /auth/me', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse({ id: '1', email: 'x@y.dev', created_at: '2026-01-01' }))
    await getMe()
    expect(apiFetch).toHaveBeenCalledWith('/auth/me')
  })
})
