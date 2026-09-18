import { describe, expect, it, vi, beforeEach } from 'vitest'
import { listPolicies, uploadPolicy, viewPolicy, deletePolicy } from '@/api/policies'
import { apiFetch } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiFetch: vi.fn(),
}))

function mockResponse(body: unknown) {
  return { json: () => Promise.resolve(body), blob: () => Promise.resolve(body) } as Response
}

describe('api/policies', () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset()
  })

  it('listPolicies GETs /policies', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse([]))
    await listPolicies()
    expect(apiFetch).toHaveBeenCalledWith('/policies')
  })

  it('uploadPolicy builds FormData with title and file, POSTs to /policies', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse({ id: 1 }))
    const file = new File(['%PDF'], 'Vacation.pdf', { type: 'application/pdf' })

    await uploadPolicy('Vacation Policy', file)

    const [path, init] = vi.mocked(apiFetch).mock.calls[0]
    expect(path).toBe('/policies')
    expect(init?.method).toBe('POST')
    const formData = init?.body as FormData
    expect(formData.get('title')).toBe('Vacation Policy')
    expect(formData.get('file')).toBe(file)
  })

  it('viewPolicy GETs /policies/{id} and returns a blob', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse(new Blob(['pdf'])))
    await viewPolicy(1)
    expect(apiFetch).toHaveBeenCalledWith('/policies/1')
  })

  it('deletePolicy DELETEs /policies/{id}', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse(undefined))
    await deletePolicy(1)
    expect(apiFetch).toHaveBeenCalledWith('/policies/1', { method: 'DELETE' })
  })
})
