import { useCallback, useMemo, useRef, useState } from "react"

import { Download, FileInput, Upload } from "lucide-react"

import {
  type SessionImportApplyResult,
  type SessionImportBatch,
  type SessionImportOutcome,
  type SessionImportRow,
  sessionImportsApi,
} from "@/api/endpoints/session-imports"
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
import { normalizeErrorMessage } from "@/lib/errors"
import { cn } from "@/lib/utils"
import { ApiError } from "@/types/api"

/** Rows shown per page of the review queue. */
const ROW_LIMIT = 50

/**
 * Rows written per apply call. Each row is its own DB round trip and commit,
 * so this stays small enough that one chunk reliably finishes well inside
 * the client's request timeout even against a remote, non-local database.
 */
const APPLY_CHUNK_SIZE = 50

interface ApplyProgress {
  imported: number
  failed: number
  total: number
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
  const percent = progress.total > 0 ? Math.round((done / progress.total) * 100) : 100
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
  const [sourceSystem, setSourceSystem] = useState("")
  const [keyColumn, setKeyColumn] = useState("")
  const [batch, setBatch] = useState<SessionImportBatch | null>(null)
  const [rows, setRows] = useState<SessionImportRow[]>([])
  const [filter, setFilter] = useState<SessionImportOutcome>("Accepted")
  const [busy, setBusy] = useState<"" | "staging" | "rows" | "applying" | "abandoning">("")
  const [error, setError] = useState<string | null>(null)
  const [applied, setApplied] = useState<SessionImportApplyResult | null>(null)
  const [applyProgress, setApplyProgress] = useState<ApplyProgress | null>(null)
  const applyCancelledRef = useRef(false)

  const counts = useMemo(() => (batch ? presentCounts(batch) : []), [batch])
  const accepted = batch ? outcomeCount(batch.outcome_counts, "Accepted") : 0
  const staged = batch?.status === "Staged"

  const reset = useCallback(() => {
    setFile(null)
    setBatch(null)
    setRows([])
    setApplied(null)
    setApplyProgress(null)
    setError(null)
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

  async function stage() {
    if (!file || !sourceSystem.trim()) return
    setBusy("staging")
    setError(null)
    setApplied(null)
    try {
      const result = await sessionImportsApi.stage(
        file,
        sourceSystem.trim(),
        keyColumn.trim() || undefined,
      )
      setBatch(result)
      await loadRows(result.id, "Accepted")
    } catch (cause) {
      setError(normalizeErrorMessage(cause, "Could not stage the file"))
    } finally {
      setBusy("")
    }
  }

  const downloadTemplate = async () => {
    try {
      const blob = await sessionImportsApi.getTemplate()
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement("a")
      anchor.href = url
      anchor.download = "session-import-template.csv"
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
    const totals = { imported: 0, failed: 0, remaining: accepted }
    setApplyProgress({ imported: 0, failed: 0, total: accepted })
    try {
      let done = false
      while (!done && !applyCancelledRef.current) {
        const result = await sessionImportsApi.apply(batch.id, APPLY_CHUNK_SIZE)
        totals.imported += result.imported
        totals.failed += result.failed
        totals.remaining = result.remaining
        done = result.done
        setApplyProgress({ imported: totals.imported, failed: totals.failed, total: accepted })
        setBatch(await sessionImportsApi.getBatch(batch.id))
      }
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
          <SheetDescription className="text-xs leading-relaxed text-fg/60">
            Staging writes nothing. It judges every row against the practitioners, clients, members
            and services this environment holds now, and says per row what stopped it. Applying
            writes only the accepted rows. Stage the same file again after the reference data
            improves and the rest are judged afresh.
          </SheetDescription>
        </SheetHeader>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-5">
          <div className="flex flex-wrap items-end gap-2">
            <div className="min-w-52 flex-1 space-y-1">
              <Label htmlFor="session-import-file">CSV file</Label>
              <Input
                id="session-import-file"
                type="file"
                accept=".csv,text/csv"
                disabled={busy !== "" || batch != null}
                className="h-9"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </div>
            <div className="w-44 space-y-1">
              <Label htmlFor="session-import-source">Source system</Label>
              <Input
                id="session-import-source"
                value={sourceSystem}
                placeholder="activity-log"
                disabled={busy !== "" || batch != null}
                className="h-9"
                onChange={(event) => setSourceSystem(event.target.value)}
              />
            </div>
            <div className="w-44 space-y-1">
              <Label htmlFor="session-import-key">Source id column</Label>
              <Input
                id="session-import-key"
                value={keyColumn}
                placeholder="optional"
                disabled={busy !== "" || batch != null}
                className="h-9"
                onChange={(event) => setKeyColumn(event.target.value)}
              />
            </div>
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
          <p className="text-xs text-fg-muted">
            The source system names where the extract came from; practitioner name mappings are
            recorded against it. The source id column is optional and must be unique and filled on
            every row, because a blank one would key part of the file differently; leave it empty
            and rows are keyed by file and row number. Download the template for the full column
            list with one Individual and one company-wide example row; note that "Client Type
            (Staff/Dep)" says who attended and "Client Type" is unrelated, saying whether this is a
            new or repeat client engagement. Files are limited to 10 MB.
          </p>

          {error ? <p className="text-xs text-destructive">{error}</p> : null}

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
              <RowTable rows={rows} loading={busy === "rows"} limit={ROW_LIMIT} />
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
            <Button
              type="button"
              disabled={!file || !sourceSystem.trim() || busy !== ""}
              onClick={() => void stage()}
            >
              <Upload className="mr-1.5 size-4" />
              {busy === "staging" ? "Staging…" : "Stage file"}
            </Button>
          )}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

function RowTable({
  rows,
  loading,
  limit,
}: {
  rows: SessionImportRow[]
  loading: boolean
  limit: number
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
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.row_number} className="border-fg/10">
                <TableCell className="px-2 py-1 tabular-nums text-fg-muted">
                  {row.row_number}
                </TableCell>
                <TableCell className="whitespace-nowrap px-2 py-1">
                  {row.session_date ?? "-"}
                </TableCell>
                <TableCell className="max-w-44 truncate px-2 py-1">
                  {row.raw_practitioner_name ?? "-"}
                </TableCell>
                <TableCell className="px-2 py-1 text-fg/70">
                  {row.reasons.join("; ") || "-"}
                </TableCell>
              </TableRow>
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
