import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConfirmDialog from '@/components/ConfirmDialog'

describe('ConfirmDialog', () => {
  it('renders nothing when closed', () => {
    render(
      <ConfirmDialog open={false} onOpenChange={() => {}} title="Видалити CV?" description="Опис" onConfirm={() => {}} />,
    )

    expect(screen.queryByText('Видалити CV?')).not.toBeInTheDocument()
  })

  it('shows the title/description and calls onConfirm on the confirm button', async () => {
    const onConfirm = vi.fn()
    const user = userEvent.setup()
    render(
      <ConfirmDialog
        open
        onOpenChange={() => {}}
        title="Видалити CV?"
        description="Дію не можна скасувати."
        onConfirm={onConfirm}
      />,
    )

    expect(screen.getByText('Видалити CV?')).toBeInTheDocument()
    expect(screen.getByText('Дію не можна скасувати.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Видалити' }))

    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('uses a custom confirm label when provided', () => {
    render(
      <ConfirmDialog
        open
        onOpenChange={() => {}}
        title="Заголовок"
        description="Опис"
        confirmLabel="Так, продовжити"
        onConfirm={() => {}}
      />,
    )

    expect(screen.getByRole('button', { name: 'Так, продовжити' })).toBeInTheDocument()
  })

  it('calls onOpenChange(false) when cancel is clicked, without calling onConfirm', async () => {
    const onConfirm = vi.fn()
    const onOpenChange = vi.fn()
    const user = userEvent.setup()
    render(
      <ConfirmDialog open onOpenChange={onOpenChange} title="Заголовок" description="Опис" onConfirm={onConfirm} />,
    )

    await user.click(screen.getByRole('button', { name: 'Скасувати' }))

    expect(onConfirm).not.toHaveBeenCalled()
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})
