import { describe, expect, it } from 'vitest'
import { formatDateTime } from '@/lib/format'

describe('formatDateTime', () => {
  it('formats an ISO date as day, Ukrainian month, year, HH:MM', () => {
    expect(formatDateTime('2026-09-16T14:22:30')).toBe('16 вересня 2026, 14:22')
  })

  it('pads single-digit hours and minutes with a leading zero', () => {
    expect(formatDateTime('2026-01-05T09:05:00')).toBe('5 січня 2026, 09:05')
  })
})
