import { BrowserRouter, Navigate, Route, Routes } from 'react-router'

import LoginPage from '@/features/auth/LoginPage'
import RequireAuth from '@/features/auth/RequireAuth'
import ChatPage from '@/features/chat/ChatPage'
import CandidatesPage from '@/features/candidates/CandidatesPage'
import PoliciesPage from '@/features/policies/PoliciesPage'
import JobRequirementsPage from '@/features/job-requirements/JobRequirementsPage'
import ReportsPage from '@/features/reports/ReportsPage'
import AppShell from '@/layouts/AppShell'
import { Toaster } from '@/components/ui/sonner'

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="bottom-right" />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<ChatPage />} />
            <Route path="/c/:conversationId" element={<ChatPage />} />
            <Route path="/candidates" element={<CandidatesPage />} />
            <Route path="/policies" element={<PoliciesPage />} />
            <Route path="/job-requirements" element={<JobRequirementsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
