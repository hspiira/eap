import { useCallback, useMemo, useRef, useState } from "react"

import { AlertTriangle, Download, FileInput, RefreshCw, Upload } from "lucide-react"

import { providerAliasesApi } from "@/api/endpoints/provider-aliases"
import {
  type SessionImportApplyResult,
  type SessionImportBatch,
  type SessionImportOutcome,
  type SessionImportRow,
  sessionImportsApi,
} from "@/api/endpoints/session-imports"
import { ConfirmDialog } from "@/components/common/ConfirmDialog"
import { NamePractitionerDialog } from "@/components/sessions/NamePractitionerDialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import { useCurrentRole } from "@/hooks/useCanWrite"
import { applyPace } from "@/lib/apply-progress"
import { normalizeErrorMessage } from "@/lib/errors"
import { cn } from "@/lib/utils"
import { useTenantStore } from "@/store/slices/tenantSlice"
import { ApiError } from "@/types/api"
import { TenantRole } from "@/types/enums"

/** Only Chromium browsers support a re-readable file handle; others fall back to a plain input. */
const supportsFilePicker =
  typeof window !== "undefined" && typeof window.showOpenFilePicker === "function"

interface FilePickerAcceptType {
  description?: string
  accept: Record<string, string[]>
}

interface OpenFilePickerOptions {
  types?: FilePickerAcceptType[]
  excludeAcceptAllOption?: boolean
  multiple?: boolean
}

interface FileSystemHandlePermissionDescriptor {
  mode?: "read" | "readwrite"
}

declare global {
  interface FileSystemFileHandle {
    queryPermission(descriptor?: FileSystemHandlePermissionDescriptor): Promise<PermissionState>
    requestPermission(descriptor?: FileSystemHandlePermissionDescriptor): Promise<PermissionState>
  }
  interface Window {
    showOpenFilePicker?: (options?: OpenFilePickerOptions) => Promise<FileSystemFileHandle[]>
  }
}

/**
 * The only source system this dialog has ever staged a file for: the
 * activity-log workbook the counselling team exports. Practitioner aliases
 * already resolved in this environment are recorded against this exact
 * string (see `scripts/resolve_provider_aliases.py`), so changing it would
 * silently break every practitioner name this environment already knows.
 * If a second, genuinely different source system is ever needed, this
 * becomes a real field again rather than a constant.
 */
const SOURCE_SYSTEM = "activity-log-workbook"

/** Rows shown per page of the review queue. */
const ROW_LIMIT = 50

/** Rows written per apply call, at the server's ceiling. */
const APPLY_CHUNK_SIZE = 200

interface ApplyProgress {
  imported: number
  failed: number
  total: number
  startedAt: number
}

/**
 * A chunk that timed out or dropped connection already committed on the
 * server before the response was lost in transit, so this is never data
 * loss: the next click resumes from wherever the server actually is.
 */
function applyErrorMessage(cause: unknown): string {
  if (
    cause instanceof ApiError &&
    (cause.code === "TIMEOUT_ERROR" || cause.code === "NETWORK_ERROR")
  ) {
    return "Lost the connection partway through, but nothing already written was lost. Click Apply to resume."
  }
  return normalizeErrorMessage(cause, "Could not apply the batch")
}

/** The other batch's id, when staging failed because that batch is still awaiting a decision. */
function conflictingBatchId(cause: unknown): string | null {
  if (!(cause instanceof ApiError) || cause.code !== "IMPORT_ALREADY_STAGED") return null
  return cause.details?.find((detail) => detail.field === "batch_id")?.message ?? null
}

/**
 * What each outcome means, in the order a reviewer cares about.
 *
 * Accepted first because it is what applying writes; the rest are ordered by
 * how far the row got before it stopped, so a reviewer reads the queue as a
 * sequence of steps rather than an unsorted list of failures.
 */
const OUTCOMES: { value: SessionImportOutcome; label: string; hint: string }[] = [
  { value: "Accepted", label: "Accepted", hint: "Will be written when you apply" },
  {
    value: "Duplicate",
    label: "Already imported",
    hint: "An earlier batch imported this source row",
  },
  {
    value: "UnmappedPractitioner",
    label: "Unmapped practitioner",
    hint: "Nobody has said which practitioner this name is",
  },
  {
    value: "AmbiguousPractitioner",
    label: "Ambiguous practitioner",
    hint: "The name matches more than one practitioner",
  },
  {
    value: "MissingPractitioner",
    label: "No practitioner named",
    hint: "The source row names no practitioner at all",
  },
  {
    value: "UnresolvedClient",
    label: "Unresolved client",
    hint: "The company resolves to no client or alias",
  },
  {
    value: "UnresolvedMember",
    label: "Unresolved member",
    hint: "The member is not on the client's roster",
  },
  {
    value: "UnresolvedService",
    label: "Unresolved service",
    hint: "The intervention matches no catalogue service",
  },
  { value: "Conflicting", label: "Conflicting", hint: "The row disagrees with itself" },
  { value: "Rejected", label: "Rejected", hint: "The row cannot be read" },
]

const OUTCOME_LABELS = new Map(OUTCOMES.map((o) => [o.value, o.label]))

/**
 * Outcomes where the practitioner name is what stopped the row.
 *
 * `MissingPractitioner` belongs here so the row still reads as a failure, but
 * it can never be fixed from the review: the source names nobody, so there is
 * no spelling to record against a practitioner.
 */
const NAME_FAILURES = new Set<SessionImportOutcome>([
  "UnmappedPractitioner",
  "AmbiguousPractitioner",
  "MissingPractitioner",
])

interface SessionImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onImported: () => void
}

/**
 * How many rows came out with this outcome.
 *
 * The batch response has carried the count keyed both by the wire value,
 * `Accepted`, and by the server enum's repr, `ImportRowOutcome.ACCEPTED`. A
 * reader that knows only one of them silently reports every outcome as zero,
 * which reads as "nothing to apply" rather than as a bug.
 */
function outcomeCount(counts: Record<string, number>, outcome: SessionImportOutcome): number {
  const enumName = outcome.replaceAll(/(?<!^)([A-Z])/g, "_$1").toUpperCase()
  for (const [key, value] of Object.entries(counts)) {
    if (key === outcome || key.endsWith(`.${enumName}`)) return value
  }
  return 0
}

function presentCounts(batch: SessionImportBatch): { outcome: SessionImportOutcome; n: number }[] {
  return OUTCOMES.map((o) => ({ outcome: o.value, n: outcomeCount(batch.outcome_counts, o.value) }))
    .filter((entry) => entry.n > 0)
    .sort((a, b) => b.n - a.n)
}

/** Compact, toast-style status while a chunked apply is in flight. */
function ApplyProgressBanner({
  fileName,
  progress,
  onCancel,
}: {
  fileName: string
  progress: ApplyProgress
  onCancel: () => void
}) {
  const done = progress.imported + progress.failed
  const { percent, eta } = applyPace(done, progress.total, progress.startedAt, Date.now())
  return (
    <div className="flex shrink-0 items-center gap-3 border-t border-fg/10 bg-surface px-6 py-3">
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-medium text-fg">{fileName}</p>
        <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-fg/10">
          <div
            className="h-full rounded-full bg-primary transition-[width]"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>
      <p className="shrink-0 text-xs tabular-nums text-fg-muted">
        {done} / {progress.total} · {percent}%
        {eta ? <span className="ml-1.5 tracking-normal">· {eta}</span> : null}
      </p>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-7 shrink-0 px-2 text-xs"
        onClick={onCancel}
      >
        Cancel
      </Button>
    </div>
  )
}

export function SessionImportDialog({ open, onOpenChange, onImported }: SessionImportDialogProps) {
  const toast = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [fileHandle, setFileHandle] = useState<FileSystemFileHandle | null>(null)
  const [batch, setBatch] = useState<SessionImportBatch | null>(null)
  const [rows, setRows] = useState<SessionImportRow[]>([])
  const [filter, setFilter] = useState<SessionImportOutcome>("Accepted")
  const [busy, setBusy] = useState<"" | "staging" | "rows" | "applying" | "abandoning">("")
  const [error, setError] = useState<string | null>(null)
  const [applied, setApplied] = useState<SessionImportApplyResult | null>(null)
  const [applyProgress, setApplyProgress] = useState<ApplyProgress | null>(null)
  const [conflictBatchId, setConflictBatchId] = useState<string | null>(null)
  const [discarding, setDiscarding] = useState(false)
  const [confirmDiscardOpen, setConfirmDiscardOpen] = useState(false)
  const [namingRow, setNamingRow] = useState<string | null>(null)
  const applyCancelledRef = useRef(false)
  const tenantId = useTenantStore((state) => state.currentTenantId)
  const isAdmin = useCurrentRole() === TenantRole.ADMIN

  /**
   * Record who a stalled name is, from inside the review.
   *
   * Leaves the batch alone on purpose: its rows carry the outcome they were
   * judged with, and only staging the file again re-judges them.
   */
  const nameThePractitioner = async (providerId: string) => {
    if (!tenantId || !namingRow) return
    try {
      const { claimed } = await providerAliasesApi.adopt(
        tenantId,
        SOURCE_SYSTEM,
        namingRow,
        providerId,
      )
      toast.showSuccess(
        claimed
          ? `${namingRow} recorded. Stage the file again to re-judge its rows.`
          : `${namingRow} is already resolved to another practitioner; left as it is.`,
      )
      setNamingRow(null)
    } catch (err) {
      toast.showError(normalizeErrorMessage(err, `Could not record ${namingRow}`))
    }
  }

  const counts = useMemo(() => (batch ? presentCounts(batch) : []), [batch])
  const accepted = batch ? outcomeCount(batch.outcome_counts, "Accepted") : 0
  const staged = batch?.status === "Staged"

  const reset = useCallback(() => {
    setFile(null)
    setFileHandle(null)
    setBatch(null)
    setRows([])
    setApplied(null)
    setApplyProgress(null)
    setError(null)
    setConflictBatchId(null)
    setFilter("Accepted")
  }, [])

  const loadRows = useCallback(async (batchId: string, outcome: SessionImportOutcome) => {
    setBusy("rows")
    setFilter(outcome)
    try {
      const page = await sessionImportsApi.listRows(batchId, { outcome, limit: ROW_LIMIT })
      setRows(page.items)
    } catch (cause) {
      setError(normalizeErrorMessage(cause, "Could not load the rows"))
    } finally {
      setBusy("")
    }
  }, [])

  const selectFile = (selected: File | null, handle: FileSystemFileHandle | null = null) => {
    setFile(selected)
    setFileHandle(handle)
    setBatch(null)
    setRows([])
    setApplied(null)
    setError(null)
    setConflictBatchId(null)
  }

  const pickFile = async () => {
    if (!window.showOpenFilePicker) return
    try {
      const [handle] = await window.showOpenFilePicker({
        types: [
          {
            description: "CSV or Excel",
            accept: {
              "text/csv": [".csv"],
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
            },
          },
        ],
        excludeAcceptAllOption: false,
        multiple: false,
      })
      selectFile(await handle.getFile(), handle)
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return
      setError(normalizeErrorMessage(cause, "Could not open the file"))
    }
  }

  /** Re-reads the same handle from disk, so local edits show up without reopening the picker. */
  const refreshFile = async () => {
    if (!fileHandle) return
    try {
      const permission = await fileHandle.queryPermission({ mode: "read" })
      if (
        permission !== "granted" &&
        (await fileHandle.requestPermission({ mode: "read" })) !== "granted"
      ) {
        setError("Permission to re-read the file was denied")
        return
      }
      selectFile(await fileHandle.getFile(), fileHandle)
    } catch (cause) {
      setError(normalizeErrorMessage(cause, "Could not refresh the file"))
    }
  }

  async function stage() {
    if (!file) return
    setBusy("staging")
    setError(null)
    setApplied(null)
    try {
      const result = await sessionImportsApi.stage(file, SOURCE_SYSTEM)
      setBatch(result)
      setConflictBatchId(null)
      await loadRows(result.id, "Accepted")
    } catch (cause) {
      setError(normalizeErrorMessage(cause, "Could not stage the file"))
      setConflictBatchId(conflictingBatchId(cause))
    } finally {
      setBusy("")
    }
  }

  /** Abandons the batch blocking this file, then retries staging it. */
  const discardStuckBatch = async () => {
    if (!conflictBatchId) return
    setDiscarding(true)
    try {
      await sessionImportsApi.abandon(
        conflictBatchId,
        "Discarded from the import dialog after a restage conflict",
      )
      setConflictBatchId(null)
      await stage()
    } catch (cause) {
      setError(normalizeErrorMessage(cause, "Could not discard the stuck batch"))
    } finally {
      setDiscarding(false)
    }
  }

  const downloadTemplate = async () => {
    try {
      const blob = await sessionImportsApi.getTemplate()
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement("a")
      anchor.href = url
      anchor.download = "session-import-template.xlsx"
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (cause) {
      toast.showError(normalizeErrorMessage(cause, "Could not download the session template"))
    }
  }

  const cancelApply = () => {
    applyCancelledRef.current = true
  }

  async function apply() {
    if (!batch) return
    applyCancelledRef.current = false
    setBusy("applying")
    setError(null)
    const startedAt = Date.now()
    const totals = { imported: 0, failed: 0, remaining: accepted }
    setApplyProgress({ imported: 0, failed: 0, total: accepted, startedAt })
    try {
      let done = false
      while (!done && !applyCancelledRef.current) {
        const result = await sessionImportsApi.apply(batch.id, APPLY_CHUNK_SIZE)
        totals.imported += result.imported
        totals.failed += result.failed
        totals.remaining = result.remaining
        done = result.done
        setApplyProgress({
          imported: totals.imported,
          failed: totals.failed,
          total: accepted,
          startedAt,
        })
      }
      setBatch(await sessionImportsApi.getBatch(batch.id))
      const result: SessionImportApplyResult = { batch_id: batch.id, done, ...totals }
      setApplied(result)
      if (totals.imported > 0) onImported()
      if (done) {
        if (totals.failed === 0) toast.showSuccess(`Imported ${totals.imported} sessions`)
        else
          toast.showError(
            `${totals.failed} row${totals.failed === 1 ? "" : "s"} could not be written`,
          )
        await loadRows(batch.id, filter)
      }
    } catch (cause) {
      // Each row commits on the server as it writes, independently of
      // whether this call's response ever arrives, so a failed chunk (a
      // timeout, a dropped connection) never loses rows already written.
      // Refresh so the batch and the Apply button reflect whatever landed.
      const refreshed = await sessionImportsApi.getBatch(batch.id).catch(() => null)
      if (refreshed) setBatch(refreshed)
      if (totals.imported > 0) onImported()
      setError(applyErrorMessage(cause))
    } finally {
      setBusy("")
      setApplyProgress(null)
    }
  }

  async function abandon() {
    if (!batch) return
    const reason = window.prompt("Why is this batch not being applied?")?.trim()
    if (!reason) return
    setBusy("abandoning")
    setError(null)
    try {
      setBatch(await sessionImportsApi.abandon(batch.id, reason))
      toast.showSuccess("Batch abandoned. The file can be staged again.")
    } catch (cause) {
      setError(normalizeErrorMessage(cause, "Could not abandon the batch"))
    } finally {
      setBusy("")
    }
  }

  return (
    <Sheet
      open={open}
      onOpenChange={(next) => {
        if (!next) reset()
        onOpenChange(next)
      }}
    >
      <SheetContent
        side="right"
        className="flex h-full w-full flex-col gap-0 rounded-none border-l border-fg/15 bg-bg p-0 shadow-lg sm:max-w-2xl lg:max-w-4xl"
        onPointerDownOutside={(event) => event.preventDefault()}
      >
        <SheetHeader className="shrink-0 border-b border-fg/10 px-6 py-5 pr-14 text-left">
          <SheetTitle className="text-base text-fg">Import sessions</SheetTitle>
          <SheetDescription asChild>
            <ul className="list-disc space-y-1 pl-4 text-xs leading-relaxed text-fg/60">
              <li>Staging writes nothing.</li>
              <li>
                Every row is judged against the practitioners, clients, members and services this
                environment holds now, and each row says what stopped it.
              </li>
              <li>Applying writes only the accepted rows.</li>
              <li>
                Stage the same file again after the reference data improves and the rest are judged
                afresh.
              </li>
            </ul>
          </SheetDescription>
        </SheetHeader>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-5">
          <div className="flex flex-wrap items-center gap-2">
            <Label htmlFor="session-import-file" className="shrink-0">
              CSV or Excel file
            </Label>
            {supportsFilePicker ? (
              <>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={busy !== ""}
                  className="h-9 min-w-52 flex-1 justify-start truncate font-normal"
                  onClick={() => void pickFile()}
                >
                  {file ? file.name : "Choose file…"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  disabled={!fileHandle || busy !== ""}
                  title="Re-read this file from disk"
                  aria-label="Refresh CSV from disk"
                  className="h-9 w-9 shrink-0"
                  onClick={() => void refreshFile()}
                >
                  <RefreshCw className="size-3.5" />
                </Button>
              </>
            ) : (
              <Input
                id="session-import-file"
                type="file"
                accept=".csv,text/csv,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                disabled={busy !== ""}
                className="h-9 min-w-52 flex-1"
                onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
              />
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-9 shrink-0"
              onClick={() => void downloadTemplate()}
            >
              <Download className="mr-1.5 size-3.5" />
              Template
            </Button>
          </div>
          <ul className="list-disc space-y-1 pl-4 text-xs text-fg-muted">
            <li>
              Rows are judged against the activity-log workbook&apos;s practitioner, client and
              service names. Client Code, if present, is used instead of the company name.
            </li>
            <li>
              Download the template (.xlsx) for the full column list, with one Individual and one
              company-wide example row. Columns backed by a fixed or tenant list get a dropdown on a
              hidden sheet; every value is still validated server-side regardless of how it got into
              the cell.
            </li>
            <li>
              &quot;Client Type (Staff/Dep)&quot; says who attended. &quot;Client Type&quot; is
              unrelated and says whether this is a new or repeat client engagement.
            </li>
            <li>
              Issue/Topic, Diagnosis Type, Diagnosis and Approved By are optional enrichment: a row
              is still imported even if none of them resolve.
            </li>
            <li>Files are limited to 10 MB.</li>
          </ul>

          {error ? (
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-xs text-destructive">{error}</p>
              {conflictBatchId ? (
                <Button
                  type="button"
                  variant="link"
                  size="sm"
                  className="h-auto px-0 text-xs"
                  onClick={() => setConfirmDiscardOpen(true)}
                >
                  Discard the stuck batch and retry
                </Button>
              ) : null}
            </div>
          ) : null}

          {batch ? (
            <div className="space-y-3 border-t border-fg/10 pt-4">
              <p className="text-sm">
                <strong>{batch.row_count}</strong> rows staged from {batch.file_name} ·{" "}
                <span className={cn(staged ? "text-fg-muted" : "text-primary")}>
                  {batch.status}
                </span>
              </p>
              {applied ? (
                <p
                  className={cn(
                    "text-sm",
                    applied.failed > 0 ? "text-destructive" : "text-primary",
                  )}
                >
                  Imported {applied.imported} session{applied.imported === 1 ? "" : "s"}
                  {applied.failed > 0 ? `. ${applied.failed} could not be written` : ""}
                  {!applied.done
                    ? `. ${applied.remaining} still pending, click Apply to resume`
                    : ""}
                  .
                </p>
              ) : null}
              <div className="flex flex-wrap gap-1.5">
                {counts.map(({ outcome, n }) => (
                  <Button
                    key={outcome}
                    type="button"
                    variant="outline"
                    size="sm"
                    title={OUTCOMES.find((o) => o.value === outcome)?.hint}
                    onClick={() => void loadRows(batch.id, outcome)}
                    className={cn(
                      "h-7 gap-1.5 px-2.5 text-xs",
                      filter === outcome && "border-primary/40 bg-primary/10 text-primary",
                    )}
                  >
                    {OUTCOME_LABELS.get(outcome) ?? outcome}
                    <strong className="tabular-nums">{n}</strong>
                  </Button>
                ))}
              </div>
              <RowTable
                rows={rows}
                loading={busy === "rows"}
                limit={ROW_LIMIT}
                onNamePractitioner={isAdmin ? setNamingRow : undefined}
              />
            </div>
          ) : null}
        </div>

        {applyProgress ? (
          <ApplyProgressBanner
            fileName={batch?.file_name ?? "Applying import…"}
            progress={applyProgress}
            onCancel={cancelApply}
          />
        ) : null}

        <SheetFooter className="shrink-0 justify-end gap-2 border-t border-fg/10 bg-surface px-6 py-3">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          {batch && staged ? (
            <Button
              type="button"
              variant="outline"
              disabled={busy !== ""}
              onClick={() => void abandon()}
            >
              Abandon
            </Button>
          ) : null}
          {batch ? (
            <Button
              type="button"
              disabled={busy !== "" || !staged || accepted === 0}
              onClick={() => void apply()}
            >
              <FileInput className="mr-1.5 size-4" />
              {busy === "applying" ? "Applying…" : `Apply ${accepted} rows`}
            </Button>
          ) : (
            <Button type="button" disabled={!file || busy !== ""} onClick={() => void stage()}>
              <Upload className="mr-1.5 size-4" />
              {busy === "staging" ? "Staging…" : "Stage file"}
            </Button>
          )}
        </SheetFooter>
      </SheetContent>
      <ConfirmDialog
        open={confirmDiscardOpen}
        onOpenChange={setConfirmDiscardOpen}
        title="Discard the stuck batch?"
        description="This file is already staged and awaiting a decision in another batch. Discarding it may lose any review already done there, so this upload can be staged fresh."
        confirmLabel="Discard and retry"
        destructive
        loading={discarding}
        onConfirm={discardStuckBatch}
      />

      <NamePractitionerDialog
        sourceName={namingRow}
        open={namingRow !== null}
        onOpenChange={(next) => !next && setNamingRow(null)}
        onConfirm={nameThePractitioner}
      />
    </Sheet>
  )
}

function RowTable({
  rows,
  loading,
  limit,
  onNamePractitioner,
}: {
  rows: SessionImportRow[]
  loading: boolean
  limit: number
  /** Admin-only: the alias write behind it is refused for anyone else. */
  onNamePractitioner?: (sourceName: string) => void
}) {
  if (loading) return <p className="text-xs text-fg-muted">Loading rows…</p>
  if (rows.length === 0) return <p className="text-xs text-fg-muted">No rows with this outcome.</p>
  return (
    <>
      <div className="max-h-[26rem] overflow-auto rounded-sm border border-fg/10">
        <Table className="text-left text-xs">
          <TableHeader className="sticky top-0 bg-surface text-fg-muted">
            <TableRow className="border-fg/10">
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Row</TableHead>
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Date</TableHead>
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Practitioner</TableHead>
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Why</TableHead>
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">
                <span className="sr-only">Actions</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <RowLine key={row.row_number} row={row} onNamePractitioner={onNamePractitioner} />
            ))}
          </TableBody>
        </Table>
      </div>
      {rows.length === limit ? (
        <p className="text-xs text-fg-muted">
          Showing the first {limit}. Narrow the outcome to see the rest.
        </p>
      ) : null}
    </>
  )
}

/**
 * One staged row.
 *
 * A row the practitioner name stopped keeps the spelling the file used, marked
 * as the failure it is rather than quietly blank, because that spelling is what
 * has to be recognised before the row can import.
 */
function RowLine({
  row,
  onNamePractitioner,
}: {
  row: SessionImportRow
  onNamePractitioner?: (sourceName: string) => void
}) {
  const blocked = NAME_FAILURES.has(row.outcome)
  const name = row.raw_practitioner_name
  const fixable = blocked && Boolean(name) && Boolean(onNamePractitioner)

  return (
    <TableRow className="border-fg/10">
      <TableCell className="px-2 py-1 tabular-nums text-fg-muted">{row.row_number}</TableCell>
      <TableCell className="whitespace-nowrap px-2 py-1">{row.session_date ?? "-"}</TableCell>
      <TableCell
        className={cn("max-w-44 px-2 py-1", blocked ? "text-destructive" : "truncate")}
        title={blocked ? "This name stopped the row importing" : undefined}
      >
        {blocked ? (
          <span className="flex items-start gap-1">
            <AlertTriangle aria-hidden className="mt-0.5 size-3 shrink-0" />
            <span className="font-medium">{name ?? "No name in the source"}</span>
          </span>
        ) : (
          (name ?? "-")
        )}
      </TableCell>
      <TableCell className={cn("px-2 py-1", blocked ? "text-destructive/80" : "text-fg/70")}>
        {row.reasons.join("; ") || "-"}
      </TableCell>
      <TableCell className="whitespace-nowrap px-2 py-1 text-right">
        {fixable ? (
          <Button
            type="button"
            variant="link"
            size="sm"
            className="h-auto px-0 text-xs"
            onClick={() => onNamePractitioner?.(name as string)}
          >
            Name practitioner
          </Button>
        ) : null}
      </TableCell>
    </TableRow>
  )
}
