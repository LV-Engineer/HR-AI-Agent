import { describe, expect, it, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '@/App'

describe('App routing', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('redirects an unknown path through / to /login when unauthenticated', async () => {
    window.history.pushState({}, '', '/some/unknown/path')

    render(<App />)

    expect(await screen.findByLabelText('Робочий email')).toBeInTheDocument()
  })
})
