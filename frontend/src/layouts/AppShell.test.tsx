import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import AppShell from '@/layouts/AppShell'
import { getMe } from '@/api/auth'
import { listConversations } from '@/api/conversations'
import { getAccessToken, setTokens } from '@/lib/token-storage'

vi.mock('@/api/auth', () => ({
  getMe: vi.fn(),
}))

vi.mock('@/api/conversations', () => ({
  listConversations: vi.fn(),
}))

function renderShell(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Login screen</div>} />
        <Route element={<AppShell />}>
          <Route path="/" element={<div>Chat page</div>} />
          <Route path="/c/:conversationId" element={<div>Chat page</div>} />
          <Route path="/candidates" element={<div>Candidates page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

const user = { id: 'user-1', email: 'oksana.kravets@hirelume.dev', created_at: '2026-01-01T00:00:00' }

describe('AppShell', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.mocked(getMe).mockReset()
    vi.mocked(listConversations).mockReset()
  })

  it("shows the display name derived from the user's email and initials", async () => {
    vi.mocked(getMe).mockResolvedValue(user)
    vi.mocked(listConversations).mockResolvedValue([])

    renderShell('/')

    expect(await screen.findByText('Oksana Kravets')).toBeInTheDocument()
    expect(screen.getByText('OK')).toBeInTheDocument()
  })

  it('shows the conversation list and highlights the active one on a chat route', async () => {
    vi.mocked(getMe).mockResolvedValue(user)
    vi.mocked(listConversations).mockResolvedValue([
      { id: 'conv-1', title: 'Зарплати по відділах', created_at: '2026-09-16T14:22:30' },
    ])

    renderShell('/c/conv-1')

    const conversationLink = await screen.findByRole('link', { name: 'Зарплати по відділах' })
    expect(conversationLink.className).toContain('bg-accent')

    const chatNavLink = screen.getByRole('link', { name: 'Чат' })
    expect(chatNavLink.className).toContain('bg-accent')
  })

  it('does not show the conversation list on non-chat routes', async () => {
    vi.mocked(getMe).mockResolvedValue(user)
    vi.mocked(listConversations).mockResolvedValue([])

    renderShell('/candidates')

    expect(await screen.findByText('Candidates page')).toBeInTheDocument()
    expect(screen.queryByText('Розмови')).not.toBeInTheDocument()
    expect(listConversations).not.toHaveBeenCalled()
  })

  it('clears tokens and navigates to /login on logout', async () => {
    setTokens('access-1', 'refresh-1')
    vi.mocked(getMe).mockResolvedValue(user)
    vi.mocked(listConversations).mockResolvedValue([])

    const userEventInstance = userEvent.setup()
    renderShell('/')

    await screen.findByText('Chat page')
    await userEventInstance.click(screen.getByRole('button', { name: 'Вийти' }))

    expect(await screen.findByText('Login screen')).toBeInTheDocument()
    expect(getAccessToken()).toBeNull()
  })
})
