import { useState } from 'react'
import { FileText } from 'lucide-react'
import { viewReport } from '@/api/reports'

export default function ReportAttachment({ filename }: { filename: string }) {
  const [error, setError] = useState(false)

  async function handleClick() {
    try {
      const blob = await viewReport(filename)
      window.open(URL.createObjectURL(blob), '_blank')
    } catch {
      setError(true)
    }
  }

  return (
    <button onClick={handleClick} className="mt-1 flex cursor-pointer items-center gap-2 self-start text-[13.5px]">
      <FileText className="size-4 shrink-0 text-primary" />
      <span className="border-b border-foreground/30 text-foreground hover:border-foreground/60">
        {filename}
      </span>
      {error && <span className="text-destructive">не вдалося відкрити</span>}
    </button>
  )
}
