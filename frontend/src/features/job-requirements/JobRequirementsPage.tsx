import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Plus } from 'lucide-react'
import {
  listJobRequirements,
  getJobRequirement,
  createJobRequirement,
  updateJobRequirement,
  deleteJobRequirement,
  type JobRequirementSummary,
} from '@/api/job-requirements'
import { formatDateTime } from '@/lib/format'
import { cn } from 'cn'
import ConfirmDialog from '@/components/ConfirmDialog'

export default function JobRequirementsPage() {
  const [items, setItems] = useState<JobRequirementSummary[]>([])
  const [selectedId, setSelectedId] = useState<number | 'new' | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<JobRequirementSummary | null>(null)

  useEffect(() => {
    loadList()
  }, [])

  async function loadList(selectId?: number) {
    setIsLoading(true)
    try {
      const data = await listJobRequirements()
      setItems(data)
      const idToSelect = selectId ?? data[0]?.id
      if (idToSelect !== undefined) {
        openItem(idToSelect)
      } else {
        setSelectedId(null)
        setTitle('')
        setContent('')
      }
    } catch {
      setError('Не вдалося завантажити список вакансій')
    } finally {
      setIsLoading(false)
    }
  }

  async function openItem(id: number) {
    setError(null)
    try {
      const item = await getJobRequirement(id)
      setSelectedId(item.id)
      setTitle(item.title)
      setContent(item.content)
    } catch {
      setError('Не вдалося завантажити вакансію')
    }
  }

  function startNew() {
    setSelectedId('new')
    setTitle('')
    setContent('')
    setError(null)
  }

  async function handleSave() {
    if (!title.trim()) {
      setError('Вкажіть назву вакансії')
      return
    }
    setIsSaving(true)
    setError(null)
    try {
      if (selectedId === 'new') {
        const created = await createJobRequirement(title, content)
        await loadList(created.id)
        toast.success('Вакансію створено')
      } else if (selectedId !== null) {
        await updateJobRequirement(selectedId, title, content)
        await loadList(selectedId)
        toast.success('Вакансію збережено')
      }
    } catch {
      setError('Не вдалося зберегти вакансію')
      toast.error('Не вдалося зберегти вакансію')
    } finally {
      setIsSaving(false)
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    try {
      await deleteJobRequirement(deleteTarget.id)
      setDeleteTarget(null)
      await loadList()
      toast.success('Вакансію видалено')
    } catch {
      setError('Не вдалося видалити вакансію')
      setDeleteTarget(null)
      toast.error('Не вдалося видалити вакансію')
    }
  }

  return (
    <div className="flex h-full min-w-0">
      <div className="flex w-[340px] shrink-0 flex-col border-r border-border">
        <div className="flex h-[60px] shrink-0 items-center justify-between border-b border-border px-6">
          <span className="text-[14px] font-semibold text-foreground">Вакансії</span>
          <button onClick={startNew} aria-label="Додати вакансію" className="cursor-pointer text-primary hover:text-primary/80">
            <Plus className="size-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3.5">
          {isLoading ? (
            <div className="px-3 py-2 text-[13px] text-muted-foreground">Завантаження…</div>
          ) : items.length === 0 ? (
            <div className="px-3 py-2 text-[13px] text-muted-foreground">Ще немає вакансій</div>
          ) : (
            items.map((item) => (
              <button
                key={item.id}
                onClick={() => openItem(item.id)}
                className={cn(
                  'mb-1 w-full cursor-pointer rounded-[10px] px-3.5 py-3 text-left transition-colors hover:bg-accent/50',
                  item.id === selectedId && 'bg-accent',
                )}
              >
                <div
                  className={cn(
                    'text-[13.5px] text-foreground',
                    item.id === selectedId ? 'font-semibold' : 'font-medium',
                  )}
                >
                  {item.title}
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  Додано {formatDateTime(item.created_at)}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        {selectedId === null ? (
          <div className="flex h-full items-center justify-center text-[13.5px] text-muted-foreground">
            Оберіть вакансію або створіть нову
          </div>
        ) : (
          <>
            <div className="flex h-[60px] shrink-0 items-center justify-between border-b border-border px-9">
              <span className="text-[12.5px] text-muted-foreground">
                {selectedId === 'new' ? 'Нова вакансія' : 'Редагування вакансії'}
              </span>
              <div className="flex items-center gap-2.5">
                {selectedId !== 'new' && (
                  <button
                    onClick={() => {
                      const item = items.find((i) => i.id === selectedId)
                      if (item) setDeleteTarget(item)
                    }}
                    aria-label="Видалити вакансію"
                    className="cursor-pointer rounded-lg border border-destructive/50 px-4.5 py-2 text-[13px] font-semibold text-destructive transition-colors hover:bg-destructive/10"
                  >
                    Видалити
                  </button>
                )}
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="cursor-pointer rounded-lg bg-primary px-5 py-2 text-[13px] font-semibold text-primary-foreground transition-colors hover:bg-primary/80 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSaving ? 'Збереження…' : 'Зберегти'}
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-9 py-8">
              <div className="max-w-[620px]">
                {error && <div className="mb-4 text-[13px] text-destructive">{error}</div>}

                <div className="mb-5 flex flex-col gap-1.5">
                  <label htmlFor="job-title" className="text-[12.5px] font-medium text-muted-foreground">Назва вакансії</label>
                  <input
                    id="job-title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="rounded-[10px] border border-border bg-card px-[15px] py-3 text-[16px] font-semibold text-foreground outline-none"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label htmlFor="job-content" className="text-[12.5px] font-medium text-muted-foreground">Опис і вимоги (Markdown)</label>
                  <textarea
                    id="job-content"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={16}
                    className="rounded-[10px] border border-border bg-card px-[18px] py-4 text-[14px] leading-relaxed text-foreground outline-none"
                  />
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    Дані для підбору кандидатів оновлюються автоматично, тільки якщо змінено опис
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Видалити вакансію?"
        description={deleteTarget ? `Вакансію "${deleteTarget.title}" буде видалено безповоротно.` : ''}
        onConfirm={confirmDelete}
      />
    </div>
  )
}
