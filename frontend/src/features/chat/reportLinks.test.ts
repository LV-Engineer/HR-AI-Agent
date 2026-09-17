import { describe, expect, it } from 'vitest'
import { cleanReportPaths, extractReportFilenames } from '@/features/chat/reportLinks'

describe('cleanReportPaths', () => {
  it('strips the container path prefix, keeping only the filename', () => {
    const input = 'Звіт згенеровано: /app/storage/reports/report_2026-09-17_17-04-04.pdf'
    expect(cleanReportPaths(input)).toBe('Звіт згенеровано: report_2026-09-17_17-04-04.pdf')
  })

  it('leaves text without a report path untouched', () => {
    const input = 'Тут немає жодного звіту.'
    expect(cleanReportPaths(input)).toBe(input)
  })
})

describe('extractReportFilenames', () => {
  it('extracts the bare filename from a full path', () => {
    const input = 'Файл: /app/storage/reports/report_2026-09-17_17-04-04.pdf'
    expect(extractReportFilenames(input)).toEqual(['report_2026-09-17_17-04-04.pdf'])
  })

  it('deduplicates repeated mentions of the same file', () => {
    const input = 'report_2026-09-17_17-04-04.pdf ... report_2026-09-17_17-04-04.pdf'
    expect(extractReportFilenames(input)).toEqual(['report_2026-09-17_17-04-04.pdf'])
  })

  it('returns an empty array when there is no report filename', () => {
    expect(extractReportFilenames('нема звітів тут')).toEqual([])
  })
})
