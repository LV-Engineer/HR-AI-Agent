import { apiFetch } from '@/api/client'

export type CandidateCV = {
  id: string
  candidate_name: string
  uploaded_at: string
}

export async function listCvs(): Promise<CandidateCV[]> {
  const response = await apiFetch('/candidates/cv')
  return response.json()
}

export async function uploadCv(candidateName: string, file: File): Promise<CandidateCV> {
  const formData = new FormData()
  formData.append('candidate_name', candidateName)
  formData.append('file', file)
  const response = await apiFetch('/candidates/cv', { method: 'POST', body: formData })
  return response.json()
}

export async function viewCv(cvId: string): Promise<Blob> {
  const response = await apiFetch(`/candidates/cv/${cvId}`)
  return response.blob()
}

export async function deleteCv(cvId: string): Promise<void> {
  await apiFetch(`/candidates/cv/${cvId}`, { method: 'DELETE' })
}
