import { describe, expect, it, vi, beforeEach } from 'vitest'
import { listConversations, getConversationMessages, streamQuery } from '@/api/conversations'
import { apiFetch } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiFetch: vi.fn(),
}))

function mockResponse(body: unknown) {
  return { json: () => Promise.resolve(body) } as Response
}

function makeSseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
  return { body: stream } as Response
}

describe('api/conversations', () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset()
  })

  it('listConversations GETs /conversations', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse([]))
    await listConversations()
    expect(apiFetch).toHaveBeenCalledWith('/conversations')
  })

  it('getConversationMessages GETs /conversations/{id}/messages', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockResponse([]))
    await getConversationMessages('conv-1')
    expect(apiFetch).toHaveBeenCalledWith('/conversations/conv-1/messages')
  })

  it('streamQuery POSTs the question and conversation_id as JSON', async () => {
    vi.mocked(apiFetch).mockResolvedValue(makeSseResponse([]))

    const events = []
    for await (const event of streamQuery('Питання', 'conv-1')) {
      events.push(event)
    }

    expect(events).toEqual([])
    const [path, init] = vi.mocked(apiFetch).mock.calls[0]
    expect(path).toBe('/query')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({ question: 'Питання', conversation_id: 'conv-1' })
  })

  it('parses SSE "data:" lines into events, even when one is split across chunks', async () => {
    vi.mocked(apiFetch).mockResolvedValue(
      makeSseResponse([
        'data: {"type":"step","tool":"query_database","conversation_id":"conv-1"}\n\n',
        'data: {"type":"answer","content":"Ось відпо',
        'відь","conversation_id":"conv-1"}\n\n',
      ]),
    )

    const events = []
    for await (const event of streamQuery('Питання', 'conv-1')) {
      events.push(event)
    }

    expect(events).toEqual([
      { type: 'step', tool: 'query_database', conversation_id: 'conv-1' },
      { type: 'answer', content: 'Ось відповідь', conversation_id: 'conv-1' },
    ])
  })
})
