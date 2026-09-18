import { describe, expect, it, vi, beforeEach } from 'vitest'
import { listCvs, uploadCv, viewCv, deleteCv } from '@/api/candidates'
import { apiFetch } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiFetch: vi.fn(),
}))

function mockResponse(body: unknown) {
  return { json: () => Promise.resolve(body), blob: () => Promise.resolve(body) } as Response
}

describe('api/candidates', () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset()
  })

  it('listCvs GETs /candidates/cv', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse([]))
    await listCvs()
    expect(apiFetch).toHaveBeenCalledWith('/candidates/cv')
  })

  it('uploadCv builds FormData with candidate_name and file, POSTs to /candidates/cv', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse({ id: 'cv-1' }))
    const file = new File(['%PDF'], 'Ivan.pdf', { type: 'application/pdf' })

    await uploadCv('Ivan', file)

    expect(apiFetch).toHaveBeenCalledTimes(1)
    const [path, init] = vi.mocked(apiFetch).mock.calls[0]
    expect(path).toBe('/candidates/cv')
    expect(init?.method).toBe('POST')
    const formData = init?.body as FormData
    expect(formData.get('candidate_name')).toBe('Ivan')
    expect(formData.get('file')).toBe(file)
  })

  it('viewCv GETs /candidates/cv/{id} and returns a blob', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse(new Blob(['pdf'])))
    await viewCv('cv-1')
    expect(apiFetch).toHaveBeenCalledWith('/candidates/cv/cv-1')
  })

  it('deleteCv DELETEs /candidates/cv/{id}', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse(undefined))
    await deleteCv('cv-1')
    expect(apiFetch).toHaveBeenCalledWith('/candidates/cv/cv-1', { method: 'DELETE' })
  })
})
