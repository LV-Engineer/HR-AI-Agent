import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import JobRequirementsPage from '@/features/job-requirements/JobRequirementsPage'
import {
  listJobRequirements,
  getJobRequirement,
  createJobRequirement,
  updateJobRequirement,
  deleteJobRequirement,
} from '@/api/job-requirements'

vi.mock('@/api/job-requirements', () => ({
  listJobRequirements: vi.fn(),
  getJobRequirement: vi.fn(),
  createJobRequirement: vi.fn(),
  updateJobRequirement: vi.fn(),
  deleteJobRequirement: vi.fn(),
}))

describe('JobRequirementsPage', () => {
  beforeEach(() => {
    vi.mocked(listJobRequirements).mockReset()
    vi.mocked(getJobRequirement).mockReset()
    vi.mocked(createJobRequirement).mockReset()
    vi.mocked(updateJobRequirement).mockReset()
    vi.mocked(deleteJobRequirement).mockReset()
  })

  it('auto-selects and loads the first job requirement from the list', async () => {
    vi.mocked(listJobRequirements).mockResolvedValue([
      { id: 1, title: 'Backend Developer', created_at: '2026-09-14T10:00:00' },
    ])
    vi.mocked(getJobRequirement).mockResolvedValue({
      id: 1,
      title: 'Backend Developer',
      content: 'Шукаємо бекенд-розробника з досвідом Python.',
      created_at: '2026-09-14T10:00:00',
    })

    render(<JobRequirementsPage />)

    expect(await screen.findByDisplayValue('Backend Developer')).toBeInTheDocument()
    expect(screen.getByText('Шукаємо бекенд-розробника з досвідом Python.')).toBeInTheDocument()
    expect(getJobRequirement).toHaveBeenCalledWith(1)
  })

  it('creates a new job requirement and selects it after reload', async () => {
    vi.mocked(listJobRequirements)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([{ id: 5, title: 'QA Engineer', created_at: '2026-09-17T12:00:00' }])
    vi.mocked(createJobRequirement).mockResolvedValue({
      id: 5,
      title: 'QA Engineer',
      content: 'Досвід тестування',
      created_at: '2026-09-17T12:00:00',
    })
    vi.mocked(getJobRequirement).mockResolvedValue({
      id: 5,
      title: 'QA Engineer',
      content: 'Досвід тестування',
      created_at: '2026-09-17T12:00:00',
    })

    const user = userEvent.setup()
    render(<JobRequirementsPage />)

    await screen.findByText('Ще немає вакансій')
    await user.click(screen.getByRole('button', { name: 'Додати вакансію' }))

    await user.type(screen.getByLabelText('Назва вакансії'), 'QA Engineer')
    await user.type(screen.getByLabelText('Опис і вимоги (Markdown)'), 'Досвід тестування')
    await user.click(screen.getByRole('button', { name: 'Зберегти' }))

    expect(createJobRequirement).toHaveBeenCalledWith('QA Engineer', 'Досвід тестування')
    expect(await screen.findByRole('button', { name: 'Видалити вакансію' })).toBeInTheDocument()
    expect(screen.getByText('Редагування вакансії')).toBeInTheDocument()
  })

  it('saves edits to an existing job requirement', async () => {
    vi.mocked(listJobRequirements).mockResolvedValue([
      { id: 1, title: 'Backend Developer', created_at: '2026-09-14T10:00:00' },
    ])
    vi.mocked(getJobRequirement).mockResolvedValue({
      id: 1,
      title: 'Backend Developer',
      content: 'Стара версія опису.',
      created_at: '2026-09-14T10:00:00',
    })
    vi.mocked(updateJobRequirement).mockResolvedValue({
      id: 1,
      title: 'Senior Backend Developer',
      content: 'Стара версія опису. Плюс нове.',
      created_at: '2026-09-14T10:00:00',
    })

    const user = userEvent.setup()
    render(<JobRequirementsPage />)

    const titleInput = await screen.findByDisplayValue('Backend Developer')
    await user.clear(titleInput)
    await user.type(titleInput, 'Senior Backend Developer')
    await user.click(screen.getByRole('button', { name: 'Редагувати' }))
    await user.type(screen.getByLabelText('Опис і вимоги (Markdown)'), ' Плюс нове.')
    await user.click(screen.getByRole('button', { name: 'Зберегти' }))

    expect(updateJobRequirement).toHaveBeenCalledWith(
      1,
      'Senior Backend Developer',
      'Стара версія опису. Плюс нове.',
    )
  })

  it('deletes a job requirement after confirming', async () => {
    vi.mocked(listJobRequirements)
      .mockResolvedValueOnce([{ id: 1, title: 'Backend Developer', created_at: '2026-09-14T10:00:00' }])
      .mockResolvedValueOnce([])
    vi.mocked(getJobRequirement).mockResolvedValue({
      id: 1,
      title: 'Backend Developer',
      content: 'Опис вакансії.',
      created_at: '2026-09-14T10:00:00',
    })
    vi.mocked(deleteJobRequirement).mockResolvedValue(undefined)

    const user = userEvent.setup()
    render(<JobRequirementsPage />)

    await screen.findByDisplayValue('Backend Developer')
    await user.click(screen.getByRole('button', { name: 'Видалити вакансію' }))

    expect(screen.getByText('Видалити вакансію?')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Видалити' }))

    expect(deleteJobRequirement).toHaveBeenCalledWith(1)
    expect(await screen.findByText('Оберіть вакансію або створіть нову')).toBeInTheDocument()
  })
})
