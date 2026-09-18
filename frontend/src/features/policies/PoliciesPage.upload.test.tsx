import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PoliciesPage from '@/features/policies/PoliciesPage'
import { listPolicies, uploadPolicy, type HrPolicy } from '@/api/policies'

vi.mock('@/api/policies', () => ({
  listPolicies: vi.fn(),
  uploadPolicy: vi.fn(),
  viewPolicy: vi.fn(),
  deletePolicy: vi.fn(),
}))

describe('PoliciesPage upload flow', () => {
  beforeEach(() => {
    vi.mocked(listPolicies).mockResolvedValue([])
    vi.mocked(uploadPolicy).mockReset()
  })

  it('uploads a selected PDF, deriving the title from the filename', async () => {
    const uploaded: HrPolicy = { id: 1, title: 'Vacation_Policy', created_at: '2026-09-17T10:00:00' }
    vi.mocked(uploadPolicy).mockResolvedValue(uploaded)
    vi.mocked(listPolicies).mockResolvedValueOnce([]).mockResolvedValueOnce([uploaded])

    const user = userEvent.setup()
    const { container } = render(<PoliciesPage />)

    await screen.findByText('Ще немає політик')

    const file = new File(['%PDF-1.4'], 'Vacation_Policy.pdf', { type: 'application/pdf' })
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await user.upload(input, file)

    expect(uploadPolicy).toHaveBeenCalledWith('Vacation_Policy', file)
    expect(await screen.findByText('Vacation_Policy')).toBeInTheDocument()
  })

  it('rejects a non-PDF file without calling uploadPolicy', async () => {
    const { container } = render(<PoliciesPage />)

    await screen.findByText('Ще немає політик')

    const file = new File(['plain text'], 'notes.txt', { type: 'text/plain' })
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    expect(await screen.findByText('Підтримуються лише PDF-файли')).toBeInTheDocument()
    expect(uploadPolicy).not.toHaveBeenCalled()
  })
})
