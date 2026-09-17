import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CandidatesPage from '@/features/candidates/CandidatesPage'
import { listCvs, deleteCv, type CandidateCV } from '@/api/candidates'

vi.mock('@/api/candidates', () => ({
  listCvs: vi.fn(),
  uploadCv: vi.fn(),
  viewCv: vi.fn(),
  deleteCv: vi.fn(),
}))

const cv: CandidateCV = {
  id: 'cv-1',
  candidate_name: 'Іван Коваленко',
  uploaded_at: '2026-09-16T14:22:30',
}

describe('CandidatesPage delete flow', () => {
  beforeEach(() => {
    vi.mocked(listCvs).mockResolvedValue([cv])
    vi.mocked(deleteCv).mockReset()
  })

  it('cancelling the confirm dialog keeps the CV in the list', async () => {
    const user = userEvent.setup()
    render(<CandidatesPage />)

    await screen.findByText('Іван Коваленко')
    await user.click(screen.getByRole('button', { name: 'Видалити CV Іван Коваленко' }))

    expect(screen.getByText('Видалити CV?')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Скасувати' }))

    expect(deleteCv).not.toHaveBeenCalled()
    expect(screen.getByText('Іван Коваленко')).toBeInTheDocument()
  })

  it('confirming deletion calls deleteCv and removes the row', async () => {
    vi.mocked(deleteCv).mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(<CandidatesPage />)

    await screen.findByText('Іван Коваленко')
    await user.click(screen.getByRole('button', { name: 'Видалити CV Іван Коваленко' }))
    await user.click(screen.getByRole('button', { name: 'Видалити' }))

    expect(deleteCv).toHaveBeenCalledWith('cv-1')
    expect(screen.queryByText('Іван Коваленко')).not.toBeInTheDocument()
  })
})
