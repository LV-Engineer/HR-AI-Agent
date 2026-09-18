import { describe, expect, it, vi, beforeEach } from 'vitest'
import {
  listJobRequirements,
  getJobRequirement,
  createJobRequirement,
  updateJobRequirement,
  deleteJobRequirement,
} from '@/api/job-requirements'
import { apiFetch } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiFetch: vi.fn(),
}))

function mockResponse(body: unknown) {
  return { json: () => Promise.resolve(body) } as Response
}

describe('api/job-requirements', () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset()
  })

  it('listJobRequirements GETs /job-requirements', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse([]))
    await listJobRequirements()
    expect(apiFetch).toHaveBeenCalledWith('/job-requirements')
  })

  it('getJobRequirement GETs /job-requirements/{id}', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse({ id: 1 }))
    await getJobRequirement(1)
    expect(apiFetch).toHaveBeenCalledWith('/job-requirements/1')
  })

  it('createJobRequirement POSTs title and content as JSON', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse({ id: 1 }))
    await createJobRequirement('QA Engineer', 'Опис вакансії')

    const [path, init] = vi.mocked(apiFetch).mock.calls[0]
    expect(path).toBe('/job-requirements')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({ title: 'QA Engineer', content: 'Опис вакансії' })
  })

  it('updateJobRequirement PATCHes /job-requirements/{id} with title and content', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse({ id: 1 }))
    await updateJobRequirement(1, 'Senior QA Engineer', 'Оновлений опис')

    const [path, init] = vi.mocked(apiFetch).mock.calls[0]
    expect(path).toBe('/job-requirements/1')
    expect(init?.method).toBe('PATCH')
    expect(JSON.parse(init?.body as string)).toEqual({ title: 'Senior QA Engineer', content: 'Оновлений опис' })
  })

  it('deleteJobRequirement DELETEs /job-requirements/{id}', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse(undefined))
    await deleteJobRequirement(1)
    expect(apiFetch).toHaveBeenCalledWith('/job-requirements/1', { method: 'DELETE' })
  })
})
