import { apiFetch } from '@/api/client'

export type TokenPair = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type User = {
  id: string
  email: string
  created_at: string
}

export async function login(email: string, password: string): Promise<TokenPair> {
  const response = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  return response.json()
}

export async function getMe(): Promise<User> {
  const response = await apiFetch('/auth/me')
  return response.json()
}
