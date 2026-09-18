import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CandidatesPage from '@/features/candidates/CandidatesPage'
import { listCvs, deleteCv, viewCv, type CandidateCV } from '@/api/candidates'

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

describe('CandidatesPage view flow', () => {
  beforeEach(() => {
    vi.mocked(listCvs).mockResolvedValue([cv])
    vi.mocked(viewCv).mockReset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('opens the CV in a new tab when the view button is clicked', async () => {
    const blob = new Blob(['pdf'], { type: 'application/pdf' })
    vi.mocked(viewCv).mockResolvedValue(blob)
    vi.stubGlobal('open', vi.fn())
    URL.createObjectURL = vi.fn(() => 'blob:mock-url')

    const user = userEvent.setup()
    render(<CandidatesPage />)

    await screen.findByText('Іван Коваленко')
    await user.click(screen.getByRole('button', { name: 'Переглянути CV Іван Коваленко' }))

    expect(viewCv).toHaveBeenCalledWith('cv-1')
    expect(window.open).toHaveBeenCalledWith('blob:mock-url', '_blank')
  })
})
