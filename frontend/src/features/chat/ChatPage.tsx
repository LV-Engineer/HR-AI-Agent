import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { Send } from 'lucide-react'
import {
  getConversationMessages,
  streamQuery,
  type MessageResponse,
} from '@/api/conversations'
import { cn } from 'cn'
import MarkdownMessage from '@/components/MarkdownMessage'
import ReportAttachment from '@/features/chat/ReportAttachment'
import { cleanReportPaths, extractReportFilenames } from '@/features/chat/reportLinks'

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

const TOOL_LABELS: Record<string, string> = {
  get_schema: 'Аналізує структуру бази даних',
  query_database: 'Виконує запит до бази даних',
  search_hr_policy: 'Шукає в HR-політиках',
  match_candidate: 'Підбирає кандидатів',
  generate_report: 'Формує звіт',
}

function toolLabel(tool: string): string {
  return TOOL_LABELS[tool] ?? `Виконує: ${tool}`
}

const SUGGESTED_QUESTIONS = [
  'Яка середня зарплата по відділах?',
  'Скільки днів відпустки мені належить?',
  'Знайди кандидатів на позицію Backend Engineer',
  'Згенеруй звіт по плинності кадрів за квартал',
]

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId?: string }>()
  const navigate = useNavigate()

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [activeStep, setActiveStep] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!conversationId) {
      setMessages([])
      return
    }
    setError(null)
    getConversationMessages(conversationId)
      .then((history: MessageResponse[]) =>
        setMessages(history.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))),
      )
      .catch(() => setError('Не вдалося завантажити повідомлення'))
  }, [conversationId])

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, activeStep])

  async function handleSend() {
    const question = input.trim()
    if (!question || isStreaming) return

    setInput('')
    setError(null)
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setIsStreaming(true)

    try {
      let answer = ''
      let resultId = conversationId ?? null
      for await (const event of streamQuery(question, conversationId ?? null)) {
        resultId = event.conversation_id
        if (event.type === 'step') {
          setActiveStep(event.tool)
        } else if (event.type === 'answer') {
          answer = event.content
        }
      }
      setActiveStep(null)
      setMessages((prev) => [...prev, { role: 'assistant', content: answer }])

      if (!conversationId && resultId) {
        navigate(`/c/${resultId}`)
      }
    } catch {
      setActiveStep(null)
      setError('Не вдалося отримати відповідь. Спробуйте ще раз.')
    } finally {
      setIsStreaming(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-full min-w-0 flex-col">
      <div className="flex-1 overflow-y-auto px-8 py-8">
        <div className="mx-auto flex min-h-full max-w-[680px] flex-col gap-8">
          {messages.length === 0 && !isStreaming && (
            <div className="flex flex-1 flex-col items-center justify-center gap-8 text-center">
              <img src="/logo-transaparent.png" alt="" className="size-14" />
              <div>
                <div className="font-heading text-2xl font-semibold italic text-foreground">
                  Чим можу допомогти?
                </div>
                <div className="mt-2 text-[13.5px] text-muted-foreground">
                  Запитайте про персонал, зарплати, політики чи кандидатів
                </div>
              </div>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    className="cursor-pointer rounded-full border border-border bg-card px-4 py-2.5 text-[13px] text-foreground transition-colors hover:bg-accent/60"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={cn(
                'flex max-w-[85%] flex-col gap-1.5',
                m.role === 'user' ? 'self-end items-end' : 'self-start',
              )}
            >
              <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {m.role === 'user' ? 'Ви' : 'Асистент'}
              </span>
              <div
                className={cn(
                  'text-[15px] leading-relaxed text-foreground',
                  m.role === 'user' && 'whitespace-pre-wrap rounded-2xl bg-accent px-4 py-3',
                )}
              >
                {m.role === 'assistant' ? <MarkdownMessage content={cleanReportPaths(m.content)} /> : m.content}
              </div>
              {m.role === 'assistant' &&
                extractReportFilenames(m.content).map((filename) => (
                  <ReportAttachment key={filename} filename={filename} />
                ))}
            </div>
          ))}

          {isStreaming && (
            <div className="flex flex-col gap-2 self-start">
              <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Асистент
              </span>
              <span className="text-[13.5px] text-muted-foreground">
                {activeStep ? `${toolLabel(activeStep)}…` : 'Думає…'}
              </span>
            </div>
          )}

          {error && <div className="text-[13px] text-destructive">{error}</div>}

          <div ref={scrollRef} />
        </div>
      </div>

      <div className="shrink-0 pb-8">
        <div className="mx-auto flex max-w-[680px] items-center gap-3 rounded-full border border-border bg-card px-2 py-2 pl-5">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            placeholder="Напишіть запитання про персонал, зарплати чи політики компанії…"
            className="flex-1 border-none bg-transparent text-[14.5px] text-foreground outline-none placeholder:text-muted-foreground"
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="flex size-[38px] shrink-0 cursor-pointer items-center justify-center rounded-full bg-primary text-primary-foreground transition-colors hover:bg-primary/80 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send className="size-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
