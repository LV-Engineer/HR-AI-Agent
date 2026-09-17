import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import ReportsPage from '@/features/reports/ReportsPage'
import { listReports } from '@/api/reports'

vi.mock('@/api/reports', () => ({
  listReports: vi.fn(),
  viewReport: vi.fn(),
  deleteReport: vi.fn(),
}))

describe('ReportsPage', () => {
  beforeEach(() => {
    vi.mocked(listReports).mockReset()
  })

  it('renders the list of generated reports', async () => {
    vi.mocked(listReports).mockResolvedValue([
      { filename: 'report_2026-09-16_14-22-30.pdf', created_at: '2026-09-16T14:22:30' },
      { filename: 'report_2026-09-15_08-02-02.pdf', created_at: '2026-09-15T08:02:02' },
    ])

    render(<ReportsPage />)

    expect(await screen.findByText('report_2026-09-16_14-22-30.pdf')).toBeInTheDocument()
    expect(screen.getByText('report_2026-09-15_08-02-02.pdf')).toBeInTheDocument()
    expect(screen.getByText('16 вересня 2026, 14:22')).toBeInTheDocument()
  })

  it('shows an empty state when there are no reports yet', async () => {
    vi.mocked(listReports).mockResolvedValue([])

    render(<ReportsPage />)

    expect(await screen.findByText('Ще немає згенерованих звітів')).toBeInTheDocument()
  })
})
