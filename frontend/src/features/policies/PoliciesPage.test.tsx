import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PoliciesPage from '@/features/policies/PoliciesPage'
import { listPolicies, viewPolicy, type HrPolicy } from '@/api/policies'
import { ApiError } from '@/api/client'

vi.mock('@/api/policies', () => ({
  listPolicies: vi.fn(),
  uploadPolicy: vi.fn(),
  viewPolicy: vi.fn(),
  deletePolicy: vi.fn(),
}))

const policy: HrPolicy = {
  id: 1,
  title: 'Політика відпусток',
  created_at: '2026-09-16T14:22:30',
}

describe('PoliciesPage', () => {
  beforeEach(() => {
    vi.mocked(listPolicies).mockResolvedValue([policy])
    vi.mocked(viewPolicy).mockReset()
  })

  it('shows a specific message when the policy has no attached file (404)', async () => {
    vi.mocked(viewPolicy).mockRejectedValue(new ApiError(404, 'Policy not found'))
    const user = userEvent.setup()
    render(<PoliciesPage />)

    await screen.findByText('Політика відпусток')
    await user.click(screen.getByRole('button', { name: 'Переглянути політику Політика відпусток' }))

    expect(await screen.findByText('Для цієї політики немає файлу')).toBeInTheDocument()
  })

  it('shows a generic error for any other failure', async () => {
    vi.mocked(viewPolicy).mockRejectedValue(new Error('network down'))
    const user = userEvent.setup()
    render(<PoliciesPage />)

    await screen.findByText('Політика відпусток')
    await user.click(screen.getByRole('button', { name: 'Переглянути політику Політика відпусток' }))

    expect(await screen.findByText('Не вдалося відкрити файл')).toBeInTheDocument()
  })
})
