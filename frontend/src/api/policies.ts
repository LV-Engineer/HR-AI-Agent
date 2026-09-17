import { apiFetch } from '@/api/client'

export type HrPolicy = {
  id: number
  title: string
  created_at: string
}

export async function listPolicies(): Promise<HrPolicy[]> {
  const response = await apiFetch('/policies')
  return response.json()
}

export async function uploadPolicy(title: string, file: File): Promise<HrPolicy> {
  const formData = new FormData()
  formData.append('title', title)
  formData.append('file', file)
  const response = await apiFetch('/policies', { method: 'POST', body: formData })
  return response.json()
}

export async function viewPolicy(policyId: number): Promise<Blob> {
  const response = await apiFetch(`/policies/${policyId}`)
  return response.blob()
}

export async function deletePolicy(policyId: number): Promise<void> {
  await apiFetch(`/policies/${policyId}`, { method: 'DELETE' })
}
