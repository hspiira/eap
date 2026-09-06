import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"

import { documentsApi } from "@/api/endpoints/documents"
import { DocumentFileLink } from "@/components/common/DocumentFileLink"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useCanWrite } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDay } from "@/lib/format"
import { entityListKey } from "@/lib/queries"

export function ContractAttachments({ contractId }: { contractId: string }) {
  const queryClient = useQueryClient()
  const canWrite = useCanWrite()
  const [page, setPage] = useState(1)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const query = useQuery({
    queryKey: entityListKey("documents", { contract_id: contractId, page, limit: 20 }),
    queryFn: () => documentsApi.list({ contract_id: contractId, page, limit: 20 }),
  })
  const upload = async (file: File) => {
    setError(null)
    if (file.size > 10 * 1024 * 1024) {
      setError("Attachments must be 10 MB or smaller")
      return
    }
    setUploading(true)
    try {
      await documentsApi.uploadContractAttachment(contractId, file)
      setPage(1)
      await queryClient.invalidateQueries({ queryKey: ["documents"] })
    } catch (err) {
      setError(normalizeErrorMessage(err, "Could not upload attachment"))
    } finally {
      setUploading(false)
    }
  }
  return (
    <section className="space-y-4 border border-fg/10 bg-surface p-4">
      <div>
        <h2 className="text-sm font-semibold text-fg">Contract attachments</h2>
        <p className="mt-1 text-sm text-fg-muted">
          Keep signed agreements and supporting documents with this contract.
        </p>
      </div>
      {canWrite && (
        <div className="space-y-2 border-y border-fg/10 py-4">
          <label className="block text-sm font-medium" htmlFor={`attachment-${contractId}`}>
            {uploading ? "Uploading…" : "Attach a file"}
          </label>
          <Input
            id={`attachment-${contractId}`}
            type="file"
            accept=".pdf,.docx,.png,.jpg,.jpeg"
            disabled={uploading}
            onChange={(event) => {
              const file = event.currentTarget.files?.[0]
              event.currentTarget.value = ""
              if (file) void upload(file)
            }}
          />
          <p className="text-xs text-fg-muted">PDF, DOCX, PNG or JPEG. Up to 10 MB per file.</p>
        </div>
      )}
      {error && (
        <p role="alert" className="text-sm text-danger-fg">
          {error}
        </p>
      )}
      {query.isPending ? (
        <p role="status" className="text-sm text-fg-muted">
          Loading attachments…
        </p>
      ) : query.isError ? (
        <div role="alert">
          <p className="text-sm">Could not load attachments.</p>
          <Button variant="outline" size="sm" onClick={() => void query.refetch()}>
            Retry
          </Button>
        </div>
      ) : query.data.total === 0 ? (
        <p className="py-6 text-center text-sm text-fg-muted">No attachments yet.</p>
      ) : (
        <div className="divide-y divide-fg/10">
          {query.data.items.map((document) => (
            <div key={document.id} className="flex items-center justify-between gap-4 py-3">
              <div className="min-w-0">
                <p className="break-words text-sm font-medium">{document.name}</p>
                <p className="mt-1 text-xs text-fg-muted">
                  {formatDay(document.created_at)}
                  {document.file_size != null &&
                    ` · ${Math.max(1, Math.round(document.file_size / 1024))} KB`}
                </p>
              </div>
              <DocumentFileLink document={document} />
            </div>
          ))}
        </div>
      )}
      {query.data && query.data.total > 20 && (
        <div className="flex items-center justify-between text-sm">
          <span>
            Page {page} of {Math.ceil(query.data.total / 20)}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)}>
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={page * 20 >= query.data.total}
              onClick={() => setPage(page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </section>
  )
}
