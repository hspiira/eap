import { useState } from "react"

import { documentsApi } from "@/api/endpoints/documents"
import { Button } from "@/components/ui/button"
import { normalizeErrorMessage } from "@/lib/errors"
import type { Document } from "@/types/entities"

export function DocumentFileLink({ document }: { document: Document }) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const download = async () => {
    setPending(true)
    setError(null)
    try {
      const blob = await documentsApi.download(document.id)
      const url = URL.createObjectURL(blob)
      const anchor = window.document.createElement("a")
      anchor.href = url
      anchor.download = document.name
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(normalizeErrorMessage(err, "Could not download attachment"))
    } finally {
      setPending(false)
    }
  }
  if (document.file_url)
    return (
      <a
        href={document.file_url}
        target="_blank"
        rel="noreferrer"
        className="text-sm text-primary hover:underline"
      >
        Open file
      </a>
    )
  if (!document.file_path) return <span className="text-xs text-fg-muted">File unavailable</span>
  return (
    <div className="text-right">
      <Button
        size="sm"
        variant="outline"
        disabled={pending}
        onClick={() => void download()}
        aria-label={`Download ${document.name}`}
      >
        {pending ? "Downloading…" : "Download"}
      </Button>
      {error && (
        <p role="alert" className="mt-2 text-xs text-danger-fg">
          {error}
        </p>
      )}
    </div>
  )
}
