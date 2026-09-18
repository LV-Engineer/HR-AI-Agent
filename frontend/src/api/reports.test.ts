import { describe, expect, it, vi, beforeEach } from 'vitest'
import { listReports, viewReport, deleteReport } from '@/api/reports'
import { apiFetch } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiFetch: vi.fn(),
}))

function mockResponse(body: unknown) {
  return { json: () => Promise.resolve(body), blob: () => Promise.resolve(body) } as Response
}

describe('api/reports', () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset()
  })

  it('listReports GETs /reports', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse([]))
    await listReports()
    expect(apiFetch).toHaveBeenCalledWith('/reports')
  })

  it('viewReport URL-encodes the filename', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse(new Blob(['pdf'])))
    await viewReport('report with space.pdf')
    expect(apiFetch).toHaveBeenCalledWith('/reports/report%20with%20space.pdf')
  })

  it('deleteReport URL-encodes the filename and sends DELETE', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse(undefined))
    await deleteReport('report_2026-09-16_14-22-30.pdf')
    expect(apiFetch).toHaveBeenCalledWith('/reports/report_2026-09-16_14-22-30.pdf', { method: 'DELETE' })
  })
})
