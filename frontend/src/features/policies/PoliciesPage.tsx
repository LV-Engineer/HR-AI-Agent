import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Upload, Eye, Trash2, Plus } from 'lucide-react'
import { listPolicies, uploadPolicy, viewPolicy, deletePolicy, type HrPolicy } from '@/api/policies'
import { ApiError } from '@/api/client'
import { formatDateTime } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog'

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<HrPolicy[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<HrPolicy | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadPolicies()
  }, [])

  async function loadPolicies() {
    setIsLoading(true)
    try {
      const data = await listPolicies()
      setPolicies(data)
    } catch {
      setError('Не вдалося завантажити список політик')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleFile(file: File) {
    if (file.type !== 'application/pdf') {
      setError('Підтримуються лише PDF-файли')
      return
    }
    setError(null)
    setIsUploading(true)
    const title = file.name.replace(/\.pdf$/i, '')
    try {
      await uploadPolicy(title, file)
      await loadPolicies()
      toast.success('Політику завантажено')
    } catch {
      setError('Не вдалося завантажити файл')
      toast.error('Не вдалося завантажити файл')
    } finally {
      setIsUploading(false)
    }
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  async function handleView(policy: HrPolicy) {
    try {
      const blob = await viewPolicy(policy.id)
      window.open(URL.createObjectURL(blob), '_blank')
    } catch (err) {
      setError(err instanceof ApiError && err.status === 404 ? 'Для цієї політики немає файлу' : 'Не вдалося відкрити файл')
    }
  }

  function handleDelete(policy: HrPolicy) {
    setDeleteTarget(policy)
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    try {
      await deletePolicy(deleteTarget.id)
      setPolicies((prev) => prev.filter((p) => p.id !== deleteTarget.id))
      toast.success('Політику видалено')
    } catch {
      setError('Не вдалося видалити політику')
      toast.error('Не вдалося видалити політику')
    } finally {
      setDeleteTarget(null)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-[60px] shrink-0 items-center justify-between border-b border-border px-9">
        <span className="text-[14px] font-semibold text-foreground">HR-політики</span>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="flex cursor-pointer items-center gap-2 rounded-lg bg-primary px-4 py-2.5 pl-3.5 text-[13px] font-semibold text-primary-foreground transition-colors hover:bg-primary/80 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Plus className="size-3.5" />
          Завантажити політику
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-9 py-8">
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
            e.target.value = ''
          }}
        />

        <div
          onDragOver={(e) => {
            e.preventDefault()
            setIsDragging(true)
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`mb-7 flex items-center gap-3.5 rounded-xl border-[1.5px] border-dashed px-6 py-5 transition-colors ${
            isDragging ? 'border-primary bg-accent/40' : 'border-primary/40 bg-muted/60'
          }`}
        >
          <Upload className="size-5 shrink-0 text-primary" />
          <div>
            <div className="text-[13.5px] font-medium text-foreground">
              {isUploading ? (
                'Завантаження…'
              ) : (
                <>
                  Перетягніть PDF сюди, або{' '}
                  <button onClick={() => fileInputRef.current?.click()} className="cursor-pointer text-primary underline hover:text-primary/80">
                    оберіть файл
                  </button>
                </>
              )}
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              Дані для пошуку по політиках оновлюються автоматично
            </div>
          </div>
        </div>

        {error && <div className="mb-4 text-[13px] text-destructive">{error}</div>}

        {isLoading ? (
          <div className="text-[13.5px] text-muted-foreground">Завантаження…</div>
        ) : policies.length === 0 ? (
          <div className="text-[13.5px] text-muted-foreground">Ще немає політик</div>
        ) : (
          <table className="w-full border-collapse text-[13.5px]">
            <thead>
              <tr>
                <td className="border-b border-border px-1 py-2.5 font-medium text-muted-foreground">Назва</td>
                <td className="border-b border-border px-1 py-2.5 font-medium text-muted-foreground">Додано</td>
                <td className="w-20 border-b border-border px-1 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {policies.map((policy) => (
                <tr key={policy.id}>
                  <td className="border-b border-border/60 px-1 py-3.5 font-medium text-foreground">
                    {policy.title}
                  </td>
                  <td className="border-b border-border/60 px-1 py-3.5 text-muted-foreground">
                    {formatDateTime(policy.created_at)}
                  </td>
                  <td className="border-b border-border/60 px-1 py-3.5 text-right">
                    <button onClick={() => handleView(policy)} aria-label={`Переглянути політику ${policy.title}`} className="mr-3.5 cursor-pointer text-muted-foreground hover:text-foreground">
                      <Eye className="size-[15px]" />
                    </button>
                    <button onClick={() => handleDelete(policy)} aria-label={`Видалити політику ${policy.title}`} className="cursor-pointer text-destructive/70 hover:text-destructive">
                      <Trash2 className="size-[15px]" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Видалити політику?"
        description={deleteTarget ? `Політику "${deleteTarget.title}" буде видалено безповоротно.` : ''}
        onConfirm={confirmDelete}
      />
    </div>
  )
}
