import { Navigate, Outlet } from 'react-router'
import { getAccessToken } from '@/lib/token-storage'

export default function RequireAuth() {
  const token = getAccessToken()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
