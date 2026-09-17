import { apiFetch } from '@/api/client'

export type ConversationSummary = {
  id: string
  title: string
  created_at: string
}

export type MessageResponse = {
  role: string
  content: string
  created_at: string
}

export type QueryEvent =
  | { type: 'step'; tool: string; conversation_id: string }
  | { type: 'answer'; content: string; conversation_id: string }

export async function listConversations(): Promise<ConversationSummary[]> {
  const response = await apiFetch('/conversations')
  return response.json()
}

export async function getConversationMessages(conversationId: string): Promise<MessageResponse[]> {
  const response = await apiFetch(`/conversations/${conversationId}/messages`)
  return response.json()
}

export async function* streamQuery(
  question: string,
  conversationId: string | null,
): AsyncGenerator<QueryEvent> {
  const response = await apiFetch('/query', {
    method: 'POST',
    body: JSON.stringify({ question, conversation_id: conversationId }),
  })

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const part of parts) {
      const line = part.trim()
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice('data: '.length)) as QueryEvent
      }
    }
  }
}
