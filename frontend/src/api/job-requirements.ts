import { apiFetch } from '@/api/client'

export type JobRequirementSummary = {
  id: number
  title: string
  created_at: string
}

export type JobRequirement = {
  id: number
  title: string
  content: string
  created_at: string
}

export async function listJobRequirements(): Promise<JobRequirementSummary[]> {
  const response = await apiFetch('/job-requirements')
  return response.json()
}

export async function getJobRequirement(id: number): Promise<JobRequirement> {
  const response = await apiFetch(`/job-requirements/${id}`)
  return response.json()
}

export async function createJobRequirement(title: string, content: string): Promise<JobRequirement> {
  const response = await apiFetch('/job-requirements', {
    method: 'POST',
    body: JSON.stringify({ title, content }),
  })
  return response.json()
}

export async function updateJobRequirement(id: number, title: string, content: string): Promise<JobRequirement> {
  const response = await apiFetch(`/job-requirements/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ title, content }),
  })
  return response.json()
}

export async function deleteJobRequirement(id: number): Promise<void> {
  await apiFetch(`/job-requirements/${id}`, { method: 'DELETE' })
}
