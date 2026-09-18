import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import MarkdownMessage from '@/features/chat/MarkdownMessage'

describe('MarkdownMessage', () => {
  it('renders bold text and links', () => {
    render(<MarkdownMessage content="Це **важливо** і [посилання](https://example.com)" />)

    const strong = screen.getByText('важливо')
    expect(strong.tagName).toBe('STRONG')

    const link = screen.getByRole('link', { name: 'посилання' })
    expect(link).toHaveAttribute('href', 'https://example.com')
    expect(link).toHaveAttribute('target', '_blank')
  })

  it('renders GFM tables', () => {
    const markdown = ['| Відділ | К-сть |', '|---|---|', '| Розробка | 8 |'].join('\n')

    render(<MarkdownMessage content={markdown} />)

    expect(screen.getByRole('columnheader', { name: 'Відділ' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'Розробка' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: '8' })).toBeInTheDocument()
  })
})
