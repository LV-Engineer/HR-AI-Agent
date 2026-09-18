import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReportAttachment from '@/features/chat/ReportAttachment'
import { viewReport } from '@/api/reports'

vi.mock('@/api/reports', () => ({
  viewReport: vi.fn(),
}))

describe('ReportAttachment', () => {
  beforeEach(() => {
    vi.mocked(viewReport).mockReset()
    vi.stubGlobal('open', vi.fn())
    URL.createObjectURL = vi.fn(() => 'blob:mock-url')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('opens the report PDF in a new tab on click', async () => {
    const blob = new Blob(['pdf'], { type: 'application/pdf' })
    vi.mocked(viewReport).mockResolvedValue(blob)

    const user = userEvent.setup()
    render(<ReportAttachment filename="report_2026-09-16_14-22-30.pdf" />)

    await user.click(screen.getByRole('button', { name: /report_2026-09-16_14-22-30\.pdf/ }))

    expect(viewReport).toHaveBeenCalledWith('report_2026-09-16_14-22-30.pdf')
    expect(window.open).toHaveBeenCalledWith('blob:mock-url', '_blank')
  })

  it('shows an inline error when the report fails to load', async () => {
    vi.mocked(viewReport).mockRejectedValue(new Error('not found'))

    const user = userEvent.setup()
    render(<ReportAttachment filename="report_2026-09-16_14-22-30.pdf" />)

    await user.click(screen.getByRole('button', { name: /report_2026-09-16_14-22-30\.pdf/ }))

    expect(await screen.findByText('не вдалося відкрити')).toBeInTheDocument()
  })
})
