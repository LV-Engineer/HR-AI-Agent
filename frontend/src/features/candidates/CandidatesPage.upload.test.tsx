import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CandidatesPage from '@/features/candidates/CandidatesPage'
import { listCvs, uploadCv, type CandidateCV } from '@/api/candidates'

vi.mock('@/api/candidates', () => ({
  listCvs: vi.fn(),
  uploadCv: vi.fn(),
  viewCv: vi.fn(),
  deleteCv: vi.fn(),
}))

describe('CandidatesPage upload flow', () => {
  beforeEach(() => {
    vi.mocked(listCvs).mockResolvedValue([])
    vi.mocked(uploadCv).mockReset()
  })

  it('asks for the candidate name (prefilled from the filename) before uploading', async () => {
    const uploadedCv: CandidateCV = {
      id: 'cv-1',
      candidate_name: 'Іван Коваленко',
      uploaded_at: '2026-09-17T10:00:00',
    }
    vi.mocked(uploadCv).mockResolvedValue(uploadedCv)
    vi.mocked(listCvs).mockResolvedValueOnce([]).mockResolvedValueOnce([uploadedCv])

    const user = userEvent.setup()
    const { container } = render(<CandidatesPage />)

    await screen.findByText('Ще немає завантажених CV')

    const file = new File(['%PDF-1.4'], 'Ivan_Petrenko.pdf', { type: 'application/pdf' })
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await user.upload(input, file)

    const nameInput = await screen.findByLabelText("Ім'я кандидата")
    expect(nameInput).toHaveValue('Ivan_Petrenko')

    await user.clear(nameInput)
    await user.type(nameInput, 'Іван Коваленко')
    await user.click(screen.getByRole('button', { name: 'Завантажити' }))

    expect(uploadCv).toHaveBeenCalledWith('Іван Коваленко', file)
    expect(await screen.findByText('Іван Коваленко')).toBeInTheDocument()
  })

  it('keeps the dialog open and shows an error when the name is cleared', async () => {
    const user = userEvent.setup()
    const { container } = render(<CandidatesPage />)

    await screen.findByText('Ще немає завантажених CV')

    const file = new File(['%PDF-1.4'], 'Ivan_Petrenko.pdf', { type: 'application/pdf' })
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await user.upload(input, file)

    const nameInput = await screen.findByLabelText("Ім'я кандидата")
    await user.clear(nameInput)
    await user.click(screen.getByRole('button', { name: 'Завантажити' }))

    expect(await screen.findByText("Введіть ім'я кандидата")).toBeInTheDocument()
    expect(uploadCv).not.toHaveBeenCalled()
  })

  it('rejects a non-PDF file without opening the name dialog', async () => {
    const { container } = render(<CandidatesPage />)

    await screen.findByText('Ще немає завантажених CV')

    // fireEvent bypasses userEvent's own accept="application/pdf" filtering (which mimics the
    // native file dialog) so we can exercise the component's own file-type validation directly.
    const file = new File(['plain text'], 'notes.txt', { type: 'text/plain' })
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    expect(await screen.findByText('Підтримуються лише PDF-файли')).toBeInTheDocument()
    expect(screen.queryByLabelText("Ім'я кандидата")).not.toBeInTheDocument()
    expect(uploadCv).not.toHaveBeenCalled()
  })
})
