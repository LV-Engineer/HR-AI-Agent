import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChatPage from '@/features/chat/ChatPage'
import { getConversationMessages, streamQuery, type QueryEvent } from '@/api/conversations'

const navigateMock = vi.fn()
let paramsMock: { conversationId?: string } = {}

vi.mock('react-router', () => ({
  useNavigate: () => navigateMock,
  useParams: () => paramsMock,
}))

vi.mock('@/api/conversations', () => ({
  getConversationMessages: vi.fn(),
  streamQuery: vi.fn(),
}))

describe('ChatPage', () => {
  beforeEach(() => {
    paramsMock = {}
    navigateMock.mockClear()
    vi.mocked(getConversationMessages).mockReset()
    vi.mocked(streamQuery).mockReset()
  })

  it('loads and renders the conversation history for an existing conversation', async () => {
    paramsMock = { conversationId: 'conv-1' }
    vi.mocked(getConversationMessages).mockResolvedValue([
      { role: 'user', content: 'Стара розмова', created_at: '2026-09-01T10:00:00' },
      { role: 'assistant', content: 'Стара відповідь', created_at: '2026-09-01T10:00:05' },
    ])

    render(<ChatPage />)

    expect(await screen.findByText('Стара розмова')).toBeInTheDocument()
    expect(screen.getByText('Стара відповідь')).toBeInTheDocument()
    expect(getConversationMessages).toHaveBeenCalledWith('conv-1')
  })

  it('streams a new answer with tool-step progress, then navigates to the new conversation', async () => {
    let resolveStep!: () => void
    let resolveAnswer!: () => void
    const stepReady = new Promise<void>((r) => (resolveStep = r))
    const answerReady = new Promise<void>((r) => (resolveAnswer = r))

    vi.mocked(streamQuery).mockImplementation(async function* (): AsyncGenerator<QueryEvent> {
      await stepReady
      yield { type: 'step', tool: 'query_database', conversation_id: 'conv-new' }
      await answerReady
      yield { type: 'answer', content: 'Ось відповідь', conversation_id: 'conv-new' }
    })

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(
      screen.getByPlaceholderText(/Напишіть запитання/),
      'Скільки у нас співробітників?{Enter}',
    )

    expect(screen.getByText('Скільки у нас співробітників?')).toBeInTheDocument()
    expect(await screen.findByText('Думає…')).toBeInTheDocument()

    resolveStep()
    expect(await screen.findByText('Виконує запит до бази даних…')).toBeInTheDocument()

    resolveAnswer()
    expect(await screen.findByText('Ось відповідь')).toBeInTheDocument()
    expect(navigateMock).toHaveBeenCalledWith('/c/conv-new')
  })

  it('does not navigate if the page was left before the stream for a new conversation finished', async () => {
    let resolveAnswer!: () => void
    const answerReady = new Promise<void>((r) => (resolveAnswer = r))

    vi.mocked(streamQuery).mockImplementation(async function* (): AsyncGenerator<QueryEvent> {
      await answerReady
      yield { type: 'answer', content: 'Ось відповідь', conversation_id: 'conv-new' }
    })

    const user = userEvent.setup()
    const { unmount } = render(<ChatPage />)

    await user.type(screen.getByPlaceholderText(/Напишіть запитання/), 'Питання{Enter}')
    unmount()

    resolveAnswer()
    // let the resumed async generator and the rest of handleSend's promise chain flush
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('shows a generic error message when the stream fails', async () => {
    vi.mocked(streamQuery).mockImplementation(() => {
      throw new Error('network down')
    })

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByPlaceholderText(/Напишіть запитання/), 'Питання{Enter}')

    expect(
      await screen.findByText('Не вдалося отримати відповідь. Спробуйте ще раз.'),
    ).toBeInTheDocument()
  })

  it('fills the input when a suggested question chip is clicked, without sending it', async () => {
    const user = userEvent.setup()
    render(<ChatPage />)

    const chip = await screen.findByRole('button', { name: 'Яка середня зарплата по відділах?' })
    await user.click(chip)

    expect(screen.getByPlaceholderText(/Напишіть запитання/)).toHaveValue(
      'Яка середня зарплата по відділах?',
    )
    expect(streamQuery).not.toHaveBeenCalled()
  })
})
