import { beforeEach, describe, expect, it } from 'vitest'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/lib/token-storage'

describe('token-storage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns null when nothing is stored', () => {
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })

  it('setTokens stores both tokens under namespaced keys', () => {
    setTokens('access-123', 'refresh-456')

    expect(getAccessToken()).toBe('access-123')
    expect(getRefreshToken()).toBe('refresh-456')
    expect(localStorage.getItem('hirelume.access_token')).toBe('access-123')
  })

  it('clearTokens removes both tokens', () => {
    setTokens('access-123', 'refresh-456')
    clearTokens()

    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })
})
