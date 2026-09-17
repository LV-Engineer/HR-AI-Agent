import { apiFetch } from '@/api/client'

export type ReportSummary = {
  filename: string
  created_at: string
}

export async function listReports(): Promise<ReportSummary[]> {
  const response = await apiFetch('/reports')
  return response.json()
}

export async function viewReport(filename: string): Promise<Blob> {
  const response = await apiFetch(`/reports/${encodeURIComponent(filename)}`)
  return response.blob()
}

export async function deleteReport(filename: string): Promise<void> {
  await apiFetch(`/reports/${encodeURIComponent(filename)}`, { method: 'DELETE' })
}
