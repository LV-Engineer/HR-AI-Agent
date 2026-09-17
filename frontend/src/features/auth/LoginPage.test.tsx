import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from '@/features/auth/LoginPage'
import { login } from '@/api/auth'
import { ApiError } from '@/api/client'
import { getAccessToken, getRefreshToken } from '@/lib/token-storage'

const navigateMock = vi.fn()

vi.mock('react-router', () => ({
  useNavigate: () => navigateMock,
}))

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear()
    navigateMock.mockClear()
    vi.mocked(login).mockReset()
  })

  it('shows a validation error for an invalid email and does not call login', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Робочий email'), 'not-an-email')
    await user.type(screen.getByLabelText('Пароль'), 'somepassword')
    await user.click(screen.getByRole('button', { name: 'Увійти' }))

    expect(await screen.findByText('Некоректний формат email')).toBeInTheDocument()
    expect(login).not.toHaveBeenCalled()
  })

  it('stores tokens and navigates to / on successful login', async () => {
    vi.mocked(login).mockResolvedValue({
      access_token: 'access-1',
      refresh_token: 'refresh-1',
      token_type: 'bearer',
    })
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Робочий email'), 'oksana.kravets@hirelume.dev')
    await user.type(screen.getByLabelText('Пароль'), 'correct-password')
    await user.click(screen.getByRole('button', { name: 'Увійти' }))

    await waitFor(() => expect(navigateMock).toHaveBeenCalledWith('/'))
    expect(getAccessToken()).toBe('access-1')
    expect(getRefreshToken()).toBe('refresh-1')
  })

  it('shows a credentials error on 401 and does not navigate', async () => {
    vi.mocked(login).mockRejectedValue(new ApiError(401, 'Invalid credentials'))
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Робочий email'), 'oksana.kravets@hirelume.dev')
    await user.type(screen.getByLabelText('Пароль'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: 'Увійти' }))

    expect(await screen.findByText('Невірний email або пароль')).toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })
})
