import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Upload, Eye, Trash2, Plus } from 'lucide-react'
import { listCvs, uploadCv, viewCv, deleteCv, type CandidateCV } from '@/api/candidates'
import { formatDateTime } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function CandidatesPage() {
  const [cvs, setCvs] = useState<CandidateCV[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<CandidateCV | null>(null)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [candidateNameInput, setCandidateNameInput] = useState('')
  const [nameError, setNameError] = useState<string | null>(null)
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

  function handleFile(file: File) {
    if (file.type !== 'application/pdf') {
      setError('Підтримуються лише PDF-файли')
      return
    }
    setError(null)
    setNameError(null)
    setCandidateNameInput(file.name.replace(/\.pdf$/i, ''))
    setPendingFile(file)
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  async function confirmUpload(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault()
    const candidateName = candidateNameInput.trim()
    if (!candidateName) {
      setNameError("Введіть ім'я кандидата")
      return
    }
    if (!pendingFile) return

    setIsUploading(true)
    try {
      await uploadCv(candidateName, pendingFile)
      await loadCvs()
      toast.success('CV завантажено')
      setPendingFile(null)
    } catch {
      setError('Не вдалося завантажити файл')
      toast.error('Не вдалося завантажити файл')
    } finally {
      setIsUploading(false)
    }
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
      toast.success('CV видалено')
    } catch {
      setError('Не вдалося видалити файл')
      toast.error('Не вдалося видалити файл')
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
                    <button onClick={() => handleView(cv)} aria-label={`Переглянути CV ${cv.candidate_name}`} className="mr-3.5 cursor-pointer text-muted-foreground hover:text-foreground">
                      <Eye className="size-[15px]" />
                    </button>
                    <button onClick={() => handleDelete(cv)} aria-label={`Видалити CV ${cv.candidate_name}`} className="cursor-pointer text-destructive/70 hover:text-destructive">
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

      <AlertDialog
        open={pendingFile !== null}
        onOpenChange={(open) => {
          if (!open) {
            setPendingFile(null)
            setNameError(null)
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Перед завантаженням</AlertDialogTitle>
            <AlertDialogDescription>
              Вкажіть ім'я кандидата для файлу «{pendingFile?.name}».
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="grid gap-1.5">
            <Label htmlFor="candidate-name">Ім'я кандидата</Label>
            <Input
              id="candidate-name"
              value={candidateNameInput}
              onChange={(e) => {
                setCandidateNameInput(e.target.value)
                setNameError(null)
              }}
              aria-invalid={nameError !== null}
            />
            {nameError && <div className="text-[13px] text-destructive">{nameError}</div>}
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Скасувати</AlertDialogCancel>
            <AlertDialogAction onClick={confirmUpload} disabled={isUploading}>
              {isUploading ? 'Завантаження…' : 'Завантажити'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
