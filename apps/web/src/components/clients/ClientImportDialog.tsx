import { useEffect, useState } from "react"

import { Download, FileInput, RefreshCw } from "lucide-react"

import {
  type ClientImportDecision,
  type ClientImportJob,
  type ClientImportResult,
  type ClientImportRowPreview,
  clientsApi,
} from "@/api/endpoints/clients"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { normalizeErrorMessage } from "@/lib/errors"

interface ClientImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onImported: () => void
}

const SYNCHRONOUS_LIMIT = 5 * 1024 * 1024

function downloadIssues(issues: ClientImportResult["issues"]): void {
  const escape = (value: string) => `"${value.replaceAll('"', '""')}"`
  const csv = [
    ["row", "field", "severity", "message"],
    ...issues.map((issue) => [
      String(issue.row),
      issue.field ?? "",
      issue.severity ?? "error",
      issue.message,
    ]),
  ]
    .map((row) => row.map(escape).join(","))
    .join("\n")
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }))
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = "clients-import-issues.csv"
  anchor.click()
  URL.revokeObjectURL(url)
}

function decisionsFor(rows: ClientImportRowPreview[]): Record<number, ClientImportDecision> {
  return Object.fromEntries(
    rows.map((row) => [
      row.row,
      {
        action: row.default_action,
        ...(row.matched_client_id ? { client_id: row.matched_client_id } : {}),
      },
    ]),
  )
}

function jobResult(job: ClientImportJob): ClientImportResult {
  return {
    imported: job.imported,
    skipped: job.skipped,
    failed: job.failed,
    clients: [],
    issues: job.issues,
    rows: [],
  }
}

function formatBytes(bytes: number): string {
  return bytes >= 1024 * 1024
    ? `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    : `${Math.max(1, Math.round(bytes / 1024))} KB`
}

export function ClientImportDialog({ open, onOpenChange, onImported }: ClientImportDialogProps) {
  const toast = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<ClientImportResult | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ClientImportResult | null>(null)
  const [decisions, setDecisions] = useState<Record<number, ClientImportDecision>>({})
  const [job, setJob] = useState<ClientImportJob | null>(null)
  const [history, setHistory] = useState<ClientImportJob[]>([])

  useEffect(() => {
    if (!open) {
      setFile(null)
      setPreview(null)
      setPreviewError(null)
      setPreviewLoading(false)
      setResult(null)
      setLoading(false)
      setDecisions({})
      setJob(null)
      return
    }
    void clientsApi
      .listImportJobs()
      .then((response) => setHistory(response.items))
      .catch(() => setHistory([]))
  }, [open])

  const pollJob = async (jobId: string) => {
    for (;;) {
      const current = await clientsApi.getImportJob(jobId)
      setJob(current)
      if (current.status === "completed" || current.status === "failed") {
        setResult(jobResult(current))
        setHistory((items) => [current, ...items.filter((item) => item.id !== current.id)])
        if (current.status === "completed") {
          onImported()
          toast.showSuccess(`${current.imported} client rows processed`)
        } else {
          toast.showError(current.error_message ?? "Background import failed")
        }
        return
      }
      await new Promise((resolve) => window.setTimeout(resolve, 1000))
    }
  }

  const selectFile = (selected: File | null) => {
    setFile(selected)
    setPreview(null)
    setPreviewError(null)
    setResult(null)
    setJob(null)
    setDecisions({})
    if (!selected) return

    setPreviewLoading(true)
    void clientsApi
      .importCsv(selected, true)
      .then((serverPreview) => {
        setPreview(serverPreview)
        setDecisions(decisionsFor(serverPreview.rows))
      })
      .catch((error) => setPreviewError(normalizeErrorMessage(error, "Could not preview CSV")))
      .finally(() => setPreviewLoading(false))
  }

  const updateDecision = (row: ClientImportRowPreview, action: ClientImportDecision["action"]) => {
    setDecisions((current) => ({
      ...current,
      [row.row]: {
        action,
        ...(action === "merge" && row.matched_client_id
          ? { client_id: row.matched_client_id }
          : {}),
      },
    }))
  }

  const importFile = async () => {
    if (!file || !preview) return
    setLoading(true)
    try {
      if (file.size > SYNCHRONOUS_LIMIT) {
        const queued = await clientsApi.queueImport(file, decisions)
        setJob(queued)
        setHistory((items) => [queued, ...items.filter((item) => item.id !== queued.id)])
        void pollJob(queued.id)
        return
      }
      const imported = await clientsApi.importCsv(file, false, decisions)
      setResult(imported)
      if (imported.imported > 0) onImported()
      if (imported.failed > 0) {
        toast.showError("Import needs attention. Review the server issue report.")
      } else {
        toast.showSuccess(`${imported.imported} client rows processed`)
      }
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not import clients"))
    } finally {
      setLoading(false)
    }
  }

  const retryJob = async (failedJob: ClientImportJob) => {
    setLoading(true)
    try {
      const queued = await clientsApi.retryImport(failedJob.id)
      setJob(queued)
      void pollJob(queued.id)
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not retry import"))
    } finally {
      setLoading(false)
    }
  }

  const progress =
    job && job.total_rows > 0 ? Math.round((job.processed_rows / job.total_rows) * 100) : 0

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="flex h-full w-full flex-col gap-0 rounded-none border-l border-fg/15 bg-bg p-0 shadow-lg sm:max-w-2xl lg:max-w-3xl"
        onPointerDownOutside={(event) => event.preventDefault()}
        onEscapeKeyDown={(event) => event.preventDefault()}
      >
        <SheetHeader className="shrink-0 border-b border-fg/10 px-6 py-5 pr-14 text-left">
          <SheetTitle className="text-base text-fg">Import clients</SheetTitle>
          <SheetDescription className="text-xs leading-relaxed text-fg/60">
            The server checks every row before you confirm it.
          </SheetDescription>
        </SheetHeader>

        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-5">
          <div className="space-y-2">
            <Label htmlFor="client-import-file">CSV file</Label>
            <Input
              id="client-import-file"
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
            />
            <p className="text-xs text-fg-muted">
              Files over 5 MB run in the background, with progress and retry support.
            </p>
          </div>

          {previewLoading ? (
            <p className="text-xs text-fg-muted">Checking rows on the server…</p>
          ) : null}
          {previewError ? <p className="text-xs text-destructive">{previewError}</p> : null}

          {preview ? (
            <div className="space-y-2 border-t border-fg/10 pt-4">
              <p className="text-sm">
                <strong>{preview.rows.length}</strong> rows checked ·{" "}
                <strong>{preview.failed}</strong> errors ·{" "}
                <strong>
                  {preview.issues.filter((issue) => issue.severity === "warning").length}
                </strong>{" "}
                possible matches
              </p>
              <div className="max-h-[28rem] overflow-auto rounded-sm border border-fg/10">
                <Table className="text-left text-xs">
                  <TableHeader className="sticky top-0 bg-surface text-fg-muted">
                    <TableRow>
                      <TableHead className="h-auto px-2 py-1.5 text-xs font-medium">Row</TableHead>
                      <TableHead className="h-auto px-2 py-1.5 text-xs font-medium">
                        Client
                      </TableHead>
                      <TableHead className="h-auto px-2 py-1.5 text-xs font-medium">
                        Match
                      </TableHead>
                      <TableHead className="h-auto px-2 py-1.5 text-xs font-medium">
                        Decision
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.rows.map((row) => {
                      const decision = decisions[row.row]?.action ?? row.default_action
                      return (
                        <TableRow key={row.row} className="border-fg/8">
                          <TableCell className="px-2 py-1.5 text-xs text-fg-muted">
                            {row.row}
                          </TableCell>
                          <TableCell className="max-w-56 px-2 py-1.5 text-xs text-fg">
                            <div>{row.name}</div>
                            {row.code ? <div className="text-fg-muted">{row.code}</div> : null}
                          </TableCell>
                          <TableCell className="max-w-48 px-2 py-1.5 text-xs text-fg-muted">
                            {row.matched_client_name ??
                              (row.state === "invalid" ? "Invalid" : "New")}
                          </TableCell>
                          <TableCell className="px-2 py-1.5 text-xs">
                            <Select
                              value={decision}
                              disabled={row.state === "invalid"}
                              onValueChange={(value) =>
                                updateDecision(row, value as ClientImportDecision["action"])
                              }
                            >
                              <SelectTrigger
                                aria-label={`Decision for row ${row.row}`}
                                className="h-8 rounded-sm border-fg/15 bg-bg px-2 text-xs text-fg"
                              >
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="create">Create</SelectItem>
                                <SelectItem value="skip">Skip</SelectItem>
                                {row.matched_client_id ? (
                                  <SelectItem value="merge">Merge</SelectItem>
                                ) : null}
                              </SelectContent>
                            </Select>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
              {preview.issues.length > 0 ? (
                <Button
                  type="button"
                  variant="link"
                  size="sm"
                  className="h-auto gap-1 px-0 text-xs"
                  onClick={() => downloadIssues(preview.issues)}
                >
                  <Download className="size-3" />
                  Download server issue report
                </Button>
              ) : null}
            </div>
          ) : null}

          {job && (job.status === "queued" || job.status === "processing") ? (
            <div className="space-y-2 border-t border-fg/10 pt-4 text-sm">
              <div className="flex justify-between text-xs text-fg-muted">
                <span>{job.status === "queued" ? "Queued" : "Importing"}</span>
                <span>
                  {job.processed_rows}/{job.total_rows} rows · {progress}%
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-fg/10">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          ) : null}

          {result ? (
            <div className="space-y-2 border-t border-fg/10 pt-4 text-sm">
              <p>
                <strong>{result.imported}</strong> processed · <strong>{result.skipped}</strong>{" "}
                skipped · <strong>{result.failed}</strong> errors
              </p>
              {result.issues.length > 0 ? (
                <Button
                  type="button"
                  variant="link"
                  size="sm"
                  className="h-auto gap-1 px-0 text-xs"
                  onClick={() => downloadIssues(result.issues)}
                >
                  <Download className="size-3" />
                  Download issue report
                </Button>
              ) : null}
            </div>
          ) : null}

          {history.length > 0 ? (
            <div className="space-y-2 border-t border-fg/10 pt-4">
              <h2 className="text-sm font-semibold text-fg">Recent imports</h2>
              <div className="space-y-1 text-xs">
                {history.slice(0, 5).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between gap-3 border-b border-fg/8 py-2"
                  >
                    <div className="min-w-0">
                      <div className="truncate text-fg">{item.filename}</div>
                      <div className="text-fg-muted">
                        {item.status} · {item.imported} processed · {formatBytes(item.file_size)}
                      </div>
                    </div>
                    {item.status === "failed" ? (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={loading}
                        onClick={() => void retryJob(item)}
                      >
                        <RefreshCw className="size-3" />
                        Retry
                      </Button>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <SheetFooter className="shrink-0 justify-end gap-2 border-t border-fg/10 bg-surface px-6 py-3">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button
            type="button"
            disabled={
              !file ||
              !preview ||
              previewError !== null ||
              previewLoading ||
              loading ||
              preview?.failed !== 0
            }
            onClick={() => void importFile()}
          >
            <FileInput className="mr-1.5 size-4" />
            {loading ? "Starting…" : `Confirm import${preview ? ` (${preview.rows.length})` : ""}`}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
