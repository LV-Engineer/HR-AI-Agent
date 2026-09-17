import { describe, expect, it, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import RequireAuth from '@/features/auth/RequireAuth'
import { setTokens } from '@/lib/token-storage'

function renderWithRouter(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Login screen</div>} />
        <Route element={<RequireAuth />}>
          <Route path="/" element={<div>Protected content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('RequireAuth', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('redirects to /login when there is no access token', () => {
    renderWithRouter('/')

    expect(screen.getByText('Login screen')).toBeInTheDocument()
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
  })

  it('renders the protected route content when an access token exists', () => {
    setTokens('access-1', 'refresh-1')
    renderWithRouter('/')

    expect(screen.getByText('Protected content')).toBeInTheDocument()
    expect(screen.queryByText('Login screen')).not.toBeInTheDocument()
  })
})
