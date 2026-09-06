import { useRef, useState } from "react"

import { Paperclip, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

/** Mirrors the cap the attachments tab enforces on the contract detail page. */
export const MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/**
 * Collects files to attach once the contract exists. Creation has no contract
 * id to upload against, so the form holds them and uploads after saving.
 */
export function ContractAttachmentQueue({
  files,
  onChange,
  disabled,
}: {
  files: File[]
  onChange: (files: File[]) => void
  disabled?: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)

  const add = (list: FileList | null) => {
    if (!list?.length) return
    const incoming = Array.from(list)
    const tooBig = incoming.find((f) => f.size > MAX_ATTACHMENT_BYTES)
    if (tooBig) {
      setError(`${tooBig.name} is larger than 10 MB`)
      return
    }
    setError(null)
    onChange([...files, ...incoming])
    if (inputRef.current) inputRef.current.value = ""
  }

  const remove = (index: number) => onChange(files.filter((_, i) => i !== index))

  return (
    <div className="space-y-2">
      <Input
        ref={inputRef}
        id="cf-attachments"
        type="file"
        multiple
        accept=".pdf,.docx,.png,.jpg,.jpeg"
        disabled={disabled}
        onChange={(event) => add(event.target.files)}
      />
      {error ? <p className="text-xs text-danger">{error}</p> : null}
      {files.length > 0 ? (
        <ul className="space-y-1">
          {files.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              className="flex items-center gap-2 border border-fg/10 bg-surface px-2 py-1.5"
            >
              <Paperclip className="size-3.5 shrink-0 text-fg-muted" aria-hidden />
              <span className="min-w-0 flex-1 truncate text-xs text-fg">{file.name}</span>
              <span className="shrink-0 tabular-nums text-[11px] text-fg-muted">
                {formatFileSize(file.size)}
              </span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                aria-label={`Remove ${file.name}`}
                disabled={disabled}
                onClick={() => remove(index)}
                className="size-6 shrink-0 p-0 text-fg/65"
              >
                <X className="size-3.5" />
              </Button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
