import { useEffect, useMemo, useState } from "react"

import { Download, FileInput } from "lucide-react"

import {
  type MemberImportResult,
  type MemberImportRow,
  type MemberImportRowResult,
  membersApi,
} from "@/api/endpoints/members"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
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

/** Rows per request. Small enough that the progress bar moves, large enough to not thrash. */
const BATCH_SIZE = 25

type Decision = "import" | "skip"
type Tone = "muted" | "ok" | "error"

interface MemberImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onImported: () => void
}

interface RowStatus {
  label: string
  tone: Tone
}

const TONE_CLASS: Record<Tone, string> = {
  muted: "text-fg-muted",
  ok: "text-primary",
  error: "text-destructive",
}

const RESULT_STATUS: Record<MemberImportRowResult["state"], RowStatus> = {
  imported: { label: "Imported", tone: "ok" },
  skipped: { label: "Skipped", tone: "muted" },
  duplicate: { label: "Existing member", tone: "muted" },
  invalid: { label: "Invalid", tone: "error" },
  failed: { label: "Failed", tone: "error" },
}

function downloadIssues(
  issues: MemberImportResult["issues"],
  positions: Map<number, number>,
): void {
  const escape = (value: string) => `"${value.replaceAll('"', '""')}"`
  const csv = [
    ["#", "csv_row", "field", "message"],
    ...issues.map((issue) => [
      String(positions.get(issue.row) ?? issue.row),
      String(issue.row),
      issue.field ?? "",
      issue.message,
    ]),
  ]
    .map((row) => row.map(escape).join(","))
    .join("\n")
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }))
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = "members-import-issues.csv"
  anchor.click()
  URL.revokeObjectURL(url)
}

function decisionsFor(rows: MemberImportRow[]): Record<number, Decision> {
  return Object.fromEntries(rows.map((row) => [row.row, row.default_action]))
}

/** A row the user has left set to import, and that the server found nothing wrong with. */
function isQueued(row: MemberImportRow, decision: Decision): boolean {
  return row.state === "new" && decision === "import" && row.values != null
}

function rowStatus(
  row: MemberImportRow,
  decision: Decision,
  result: MemberImportRowResult | undefined,
  running: boolean,
): RowStatus {
  if (result) {
    const status = RESULT_STATUS[result.state]
    return result.message ? { ...status, label: result.message } : status
  }
  if (row.state === "invalid") return { label: row.message ?? "Invalid", tone: "error" }
  if (row.state === "duplicate") return { label: "Existing member", tone: "muted" }
  if (decision === "skip") return { label: "Will skip", tone: "muted" }
  return { label: running ? "Waiting…" : "Ready", tone: "muted" }
}

export function MemberImportDialog({ open, onOpenChange, onImported }: MemberImportDialogProps) {
  const toast = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<MemberImportResult | null>(null)
  const [decisions, setDecisions] = useState<Record<number, Decision>>({})
  const [results, setResults] = useState<Record<number, MemberImportRowResult>>({})
  const [checking, setChecking] = useState(false)
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) return
    setFile(null)
    setPreview(null)
    setDecisions({})
    setResults({})
    setChecking(false)
    setRunning(false)
    setDone(false)
    setError(null)
  }, [open])

  const rows = preview?.rows ?? []
  const decisionFor = (row: MemberImportRow): Decision => decisions[row.row] ?? row.default_action
  const queued = useMemo(
    () => rows.filter((row) => isQueued(row, decisions[row.row] ?? row.default_action)),
    [rows, decisions],
  )
  /** Rows are numbered from 1 in the table; the CSV line number stays the wire key. */
  const positions = useMemo(() => new Map(rows.map((row, index) => [row.row, index + 1])), [rows])
  const finished = Object.keys(results).length
  const tally = Object.values(results).reduce(
    (totals, result) => ({ ...totals, [result.state]: (totals[result.state] ?? 0) + 1 }),
    {} as Record<string, number>,
  )

  const selectFile = (selected: File | null) => {
    setFile(selected)
    setPreview(null)
    setDecisions({})
    setResults({})
    setDone(false)
    setError(null)
    if (!selected) return
    setChecking(true)
    void membersApi
      .importRoster(selected, true)
      .then((checked) => {
        setPreview(checked)
        setDecisions(decisionsFor(checked.rows))
      })
      .catch((cause) => setError(normalizeErrorMessage(cause, "Could not check the CSV")))
      .finally(() => setChecking(false))
  }

  const updateDecision = (row: number, value: Decision) => {
    setDecisions((current) => ({ ...current, [row]: value }))
  }

  const downloadTemplate = async () => {
    try {
      const blob = await membersApi.getImportTemplate()
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement("a")
      anchor.href = url
      anchor.download = "members-import-template.csv"
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (cause) {
      toast.showError(normalizeErrorMessage(cause, "Could not download member template"))
    }
  }

  /** Send the confirmed rows in slices so each row's outcome lands as it happens. */
  const importRows = async () => {
    setRunning(true)
    setResults({})
    setError(null)
    let imported = 0
    try {
      for (let start = 0; start < queued.length; start += BATCH_SIZE) {
        const slice = queued.slice(start, start + BATCH_SIZE)
        const response = await membersApi.commitImport(
          slice.map((row) => ({ row: row.row, values: row.values! })),
        )
        imported += response.results.filter((result) => result.state === "imported").length
        setResults((current) => ({
          ...current,
          ...Object.fromEntries(response.results.map((result) => [result.row, result])),
        }))
      }
      setDone(true)
      if (imported > 0) onImported()
      if (imported === queued.length) toast.showSuccess(`${imported} member rows imported`)
      else toast.showError(`${queued.length - imported} of ${queued.length} rows need attention`)
    } catch (cause) {
      setError(normalizeErrorMessage(cause, "Could not import members"))
      if (imported > 0) onImported()
    } finally {
      setRunning(false)
    }
  }

  const progress = queued.length > 0 ? Math.round((finished / queued.length) * 100) : 0

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="flex h-full w-full flex-col gap-0 rounded-none border-l border-fg/15 bg-bg p-0 shadow-lg sm:max-w-2xl lg:max-w-4xl"
        onPointerDownOutside={(event) => event.preventDefault()}
        onEscapeKeyDown={(event) => event.preventDefault()}
      >
        <SheetHeader className="shrink-0 border-b border-fg/10 px-6 py-5 pr-14 text-left">
          <SheetTitle className="text-base text-fg">Import members</SheetTitle>
          <SheetDescription className="text-xs leading-relaxed text-fg/60">
            Upload a roster, review every row, then confirm. Each row is imported on its own, so a
            row that fails leaves the rest untouched. Staff_ID is the stable identity key; existing
            members are never overwritten.
          </SheetDescription>
        </SheetHeader>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-5">
          <div className="flex flex-wrap items-center gap-2">
            <Label htmlFor="member-import-file" className="shrink-0">
              CSV file
            </Label>
            <Input
              id="member-import-file"
              type="file"
              accept=".csv,text/csv"
              disabled={running}
              className="h-9 min-w-52 flex-1"
              onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
            />
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
            Company Code resolves the client. Supported fields: Company Code, Staff_ID, Staff
            Number, Name of Employee, Email Address, Personal Email, Date of Birth (YYYY-MM-DD),
            Gender, Phone, National ID, Passport Number, Status, Relation, and Primary Staff ID.
            Other workforce columns are ignored; files are limited to 10 MB.
          </p>

          {checking ? <p className="text-xs text-fg-muted">Checking rows on the server…</p> : null}
          {error ? <p className="text-xs text-destructive">{error}</p> : null}

          {preview ? (
            <div className="space-y-3 border-t border-fg/10 pt-4">
              <ImportProgress
                total={queued.length}
                finished={finished}
                percent={progress}
                running={running}
                done={done}
                tally={tally}
                checked={preview.rows.length}
                invalid={preview.failed}
              />
              <div className="max-h-[28rem] overflow-auto rounded-sm border border-fg/10">
                <Table className="text-left text-xs">
                  <TableHeader className="sticky top-0 bg-surface text-fg-muted">
                    <TableRow className="border-fg/10">
                      <TableHead className="h-auto px-2 py-1 text-xs font-medium">#</TableHead>
                      <TableHead className="h-auto px-2 py-1 text-xs font-medium">Name</TableHead>
                      <TableHead className="h-auto px-2 py-1 text-xs font-medium">
                        Staff ID
                      </TableHead>
                      <TableHead className="h-auto px-2 py-1 text-xs font-medium">
                        Staff no.
                      </TableHead>
                      <TableHead className="h-auto px-2 py-1 text-xs font-medium">Client</TableHead>
                      <TableHead className="h-auto px-2 py-1 text-xs font-medium">
                        Decision
                      </TableHead>
                      <TableHead className="h-auto px-2 py-1 text-xs font-medium">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((row, index) => (
                      <ImportRow
                        key={row.row}
                        row={row}
                        position={index + 1}
                        decision={decisionFor(row)}
                        result={results[row.row]}
                        running={running}
                        locked={running || done}
                        onDecision={updateDecision}
                      />
                    ))}
                  </TableBody>
                </Table>
              </div>
              {preview.issues.length > 0 ? (
                <Button
                  type="button"
                  variant="link"
                  size="sm"
                  className="h-auto gap-1 px-0 text-xs"
                  onClick={() => downloadIssues(preview.issues, positions)}
                >
                  <Download className="size-3" />
                  Download issue report
                </Button>
              ) : null}
            </div>
          ) : null}
        </div>

        <SheetFooter className="shrink-0 justify-end gap-2 border-t border-fg/10 bg-surface px-6 py-3">
          <Button
            type="button"
            variant="outline"
            disabled={running}
            onClick={() => onOpenChange(false)}
          >
            {done ? "Done" : "Close"}
          </Button>
          <Button
            type="button"
            disabled={!file || !preview || checking || running || done || queued.length === 0}
            onClick={() => void importRows()}
          >
            <FileInput className="mr-1.5 size-4" />
            {running ? `Importing ${finished}/${queued.length}…` : `Import ${queued.length} rows`}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

function ImportProgress({
  total,
  finished,
  percent,
  running,
  done,
  tally,
  checked,
  invalid,
}: {
  total: number
  finished: number
  percent: number
  running: boolean
  done: boolean
  tally: Record<string, number>
  checked: number
  invalid: number
}) {
  if (!running && !done) {
    return (
      <p className="text-sm">
        <strong>{checked}</strong> rows checked · <strong>{total}</strong> ready ·{" "}
        <strong>{checked - total - invalid}</strong> skipped · <strong>{invalid}</strong> errors
      </p>
    )
  }
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-fg-muted">
        <span>{done ? "Import complete" : "Importing rows one at a time"}</span>
        <span>
          {finished}/{total} rows · {percent}%
        </span>
      </div>
      <Progress value={percent} />
      <p className="text-sm">
        <strong>{tally.imported ?? 0}</strong> imported ·{" "}
        <strong>{(tally.skipped ?? 0) + (tally.duplicate ?? 0)}</strong> skipped ·{" "}
        <strong>{(tally.failed ?? 0) + (tally.invalid ?? 0)}</strong> failed
      </p>
    </div>
  )
}

function ImportRow({
  row,
  position,
  decision,
  result,
  running,
  locked,
  onDecision,
}: {
  row: MemberImportRow
  position: number
  decision: Decision
  result: MemberImportRowResult | undefined
  running: boolean
  locked: boolean
  onDecision: (row: number, value: Decision) => void
}) {
  const status = rowStatus(row, decision, result, running)
  const decidable = row.state === "new"
  return (
    <TableRow className="border-fg/8">
      <TableCell className="px-2 py-1 text-xs text-fg-muted">{position}</TableCell>
      <TableCell className="max-w-44 truncate px-2 py-1 text-xs text-fg">
        {row.display_label ?? "Unnamed"}
      </TableCell>
      <TableCell className="px-2 py-1 text-xs text-fg-muted">
        {row.employer_member_id ?? "-"}
      </TableCell>
      <TableCell className="px-2 py-1 text-xs text-fg-muted">{row.staff_number ?? "-"}</TableCell>
      <TableCell className="max-w-36 truncate px-2 py-1 text-xs text-fg-muted">
        {row.client_name ?? row.client_code ?? "Unresolved"}
      </TableCell>
      <TableCell className="px-2 py-1 text-xs">
        {decidable ? (
          <Select
            value={decision}
            disabled={locked}
            onValueChange={(value) => onDecision(row.row, value as Decision)}
          >
            <SelectTrigger
              aria-label={`Decision for row ${position}`}
              className="h-7 rounded-sm border-fg/15 bg-bg px-2 text-xs text-fg"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="import">Import</SelectItem>
              <SelectItem value="skip">Skip</SelectItem>
            </SelectContent>
          </Select>
        ) : (
          <span className="text-fg-muted">-</span>
        )}
      </TableCell>
      <TableCell className={`max-w-52 truncate px-2 py-1 text-xs ${TONE_CLASS[status.tone]}`}>
        {status.label}
      </TableCell>
    </TableRow>
  )
}
