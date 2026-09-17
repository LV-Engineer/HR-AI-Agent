import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import JobRequirementsPage from '@/features/job-requirements/JobRequirementsPage'
import { listJobRequirements, getJobRequirement, createJobRequirement } from '@/api/job-requirements'

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
    expect(screen.getByDisplayValue('Шукаємо бекенд-розробника з досвідом Python.')).toBeInTheDocument()
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
    expect(await screen.findByRole('button', { name: 'Видалити' })).toBeInTheDocument()
    expect(screen.getByText('Редагування вакансії')).toBeInTheDocument()
  })
})
