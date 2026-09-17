import { useEffect, useRef, useState } from 'react'
import { Upload, Eye, Trash2, Plus } from 'lucide-react'
import { listCvs, uploadCv, viewCv, deleteCv, type CandidateCV } from '@/api/candidates'
import { formatDateTime } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog'

export default function CandidatesPage() {
  const [cvs, setCvs] = useState<CandidateCV[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<CandidateCV | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadCvs()
  }, [])

  async function loadCvs() {
    setIsLoading(true)
    try {
      const data = await listCvs()
      setCvs(data)
    } catch {
      setError('Не вдалося завантажити список CV')
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
    const candidateName = file.name.replace(/\.pdf$/i, '')
    try {
      await uploadCv(candidateName, file)
      await loadCvs()
    } catch {
      setError('Не вдалося завантажити файл')
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

  async function handleView(cv: CandidateCV) {
    try {
      const blob = await viewCv(cv.id)
      window.open(URL.createObjectURL(blob), '_blank')
    } catch {
      setError('Не вдалося відкрити файл')
    }
  }

  function handleDelete(cv: CandidateCV) {
    setDeleteTarget(cv)
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    try {
      await deleteCv(deleteTarget.id)
      setCvs((prev) => prev.filter((c) => c.id !== deleteTarget.id))
    } catch {
      setError('Не вдалося видалити файл')
    } finally {
      setDeleteTarget(null)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-[60px] shrink-0 items-center justify-between border-b border-border px-9">
        <span className="text-[14px] font-semibold text-foreground">CV кандидатів</span>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="flex cursor-pointer items-center gap-2 rounded-lg bg-primary px-4 py-2.5 pl-3.5 text-[13px] font-semibold text-primary-foreground transition-colors hover:bg-primary/80 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Plus className="size-3.5" />
          Завантажити CV
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
              Дані для пошуку та підбору кандидатів обробляються автоматично
            </div>
          </div>
        </div>

        {error && <div className="mb-4 text-[13px] text-destructive">{error}</div>}

        {isLoading ? (
          <div className="text-[13.5px] text-muted-foreground">Завантаження…</div>
        ) : cvs.length === 0 ? (
          <div className="text-[13.5px] text-muted-foreground">Ще немає завантажених CV</div>
        ) : (
          <table className="w-full border-collapse text-[13.5px]">
            <thead>
              <tr>
                <td className="border-b border-border px-1 py-2.5 font-medium text-muted-foreground">Кандидат</td>
                <td className="border-b border-border px-1 py-2.5 font-medium text-muted-foreground">Завантажено</td>
                <td className="w-20 border-b border-border px-1 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {cvs.map((cv) => (
                <tr key={cv.id}>
                  <td className="border-b border-border/60 px-1 py-3.5 font-medium text-foreground">
                    {cv.candidate_name}
                  </td>
                  <td className="border-b border-border/60 px-1 py-3.5 text-muted-foreground">
                    {formatDateTime(cv.uploaded_at)}
                  </td>
                  <td className="border-b border-border/60 px-1 py-3.5 text-right">
                    <button onClick={() => handleView(cv)} className="mr-3.5 cursor-pointer text-muted-foreground hover:text-foreground">
                      <Eye className="size-[15px]" />
                    </button>
                    <button onClick={() => handleDelete(cv)} className="cursor-pointer text-destructive/70 hover:text-destructive">
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
        title="Видалити CV?"
        description={deleteTarget ? `CV кандидата "${deleteTarget.candidate_name}" буде видалено безповоротно.` : ''}
        onConfirm={confirmDelete}
      />
    </div>
  )
}
