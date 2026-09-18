import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { FileText, Eye, Trash2 } from 'lucide-react'
import { listReports, viewReport, deleteReport, type ReportSummary } from '@/api/reports'
import { formatDateTime } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog'

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ReportSummary | null>(null)

  useEffect(() => {
    loadReports()
  }, [])

  async function loadReports() {
    setIsLoading(true)
    try {
      const data = await listReports()
      setReports(data)
    } catch {
      setError('Не вдалося завантажити список звітів')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleView(report: ReportSummary) {
    try {
      const blob = await viewReport(report.filename)
      window.open(URL.createObjectURL(blob), '_blank')
    } catch {
      setError('Не вдалося відкрити звіт')
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    try {
      await deleteReport(deleteTarget.filename)
      setReports((prev) => prev.filter((r) => r.filename !== deleteTarget.filename))
      toast.success('Звіт видалено')
    } catch {
      setError('Не вдалося видалити звіт')
      toast.error('Не вдалося видалити звіт')
    } finally {
      setDeleteTarget(null)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-[60px] shrink-0 items-center border-b border-border px-9">
        <span className="text-[14px] font-semibold text-foreground">Звіти</span>
      </div>

      <div className="flex-1 overflow-y-auto px-9 py-8">
        <div className="mb-5 max-w-[560px] text-[12.5px] leading-relaxed text-muted-foreground">
          Звіти генерує асистент прямо в чаті у відповідь на запитання. Тут — повний список усіх PDF, які
          вже було створено.
        </div>

        {error && <div className="mb-4 text-[13px] text-destructive">{error}</div>}

        {isLoading ? (
          <div className="text-[13.5px] text-muted-foreground">Завантаження…</div>
        ) : reports.length === 0 ? (
          <div className="text-[13.5px] text-muted-foreground">Ще немає згенерованих звітів</div>
        ) : (
          <table className="w-full border-collapse text-[13.5px]">
            <thead>
              <tr>
                <td className="border-b border-border px-1 py-2.5 font-medium text-muted-foreground">Звіт</td>
                <td className="w-20 border-b border-border px-1 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.filename}>
                  <td className="border-b border-border/60 px-1 py-3.5">
                    <div className="flex items-center gap-3">
                      <FileText className="size-[18px] shrink-0 text-primary" />
                      <div>
                        <div className="font-medium text-foreground">{formatDateTime(report.created_at)}</div>
                        <div className="mt-0.5 text-[11.5px] text-muted-foreground">{report.filename}</div>
                      </div>
                    </div>
                  </td>
                  <td className="border-b border-border/60 px-1 py-3.5 text-right">
                    <button onClick={() => handleView(report)} aria-label={`Переглянути звіт ${report.filename}`} className="mr-3.5 cursor-pointer text-muted-foreground hover:text-foreground">
                      <Eye className="size-[15px]" />
                    </button>
                    <button onClick={() => setDeleteTarget(report)} aria-label={`Видалити звіт ${report.filename}`} className="cursor-pointer text-destructive/70 hover:text-destructive">
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
        title="Видалити звіт?"
        description={deleteTarget ? `Файл "${deleteTarget.filename}" буде видалено безповоротно.` : ''}
        onConfirm={confirmDelete}
      />
    </div>
  )
}
