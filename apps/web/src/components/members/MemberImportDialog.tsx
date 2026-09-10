import { useEffect, useState } from "react"

import { Download, FileInput, RefreshCw } from "lucide-react"

import {
  type MemberImportBatch,
  type MemberImportRow,
  type MemberImportRowDecision,
  membersApi,
} from "@/api/endpoints/members"
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

/** A New row still set to import: the only state that gets written on apply. */
function isQueued(row: MemberImportRow): boolean {
  return row.outcome === "New" && row.decision === "import"
}

/** Outcomes no decision can change. Null when the row is still the person's to direct. */
function settledStatus(row: MemberImportRow): RowStatus | null {
  if (row.imported_member_id) return { label: "Imported", tone: "ok" }
  if (row.outcome === "Failed") return { label: row.message ?? "Failed", tone: "error" }
  if (row.outcome === "Invalid") return { label: row.message ?? "Invalid", tone: "error" }
  if (row.outcome === "Duplicate") return { label: "Existing member", tone: "muted" }
  return null
}

function rowStatus(row: MemberImportRow, applied: boolean): RowStatus {
  const settled = settledStatus(row)
  if (settled) return settled
  if (row.decision === "skip") return { label: applied ? "Skipped" : "Will skip", tone: "muted" }
  return { label: applied ? "Not imported" : "Ready", tone: "muted" }
}

function downloadIssues(rows: MemberImportRow[]): void {
  const escape = (value: string) => `"${value.replaceAll('"', '""')}"`
  const flagged = rows.filter((row) => row.outcome === "Invalid" || row.outcome === "Failed")
  const csv = [
    ["row", "message"],
    ...flagged.map((row) => [String(row.row_number), row.message ?? ""]),
  ]
    .map((line) => line.map(escape).join(","))
    .join("\n")
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }))
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = "members-import-issues.csv"
  anchor.click()
  URL.revokeObjectURL(url)
}

async function fetchAllRows(batchId: string): Promise<MemberImportRow[]> {
  const items: MemberImportRow[] = []
  let page = 1
  for (;;) {
    const response = await membersApi.listImportRows(batchId, { page, limit: 200 })
    items.push(...response.items)
    if (!response.has_more) return items
    page += 1
  }
}

function ImportControls({
  file,
  fileHandle,
  applying,
  staging,
  error,
  onPick,
  onRefresh,
  onSelectFile,
  onDownloadTemplate,
}: {
  file: File | null
  fileHandle: FileSystemFileHandle | null
  applying: boolean
  staging: boolean
  error: string | null
  onPick: () => void
  onRefresh: () => void
  onSelectFile: (file: File | null) => void
  onDownloadTemplate: () => void
}) {
  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <Label htmlFor="member-import-file" className="shrink-0">
          CSV file
        </Label>
        {supportsFilePicker ? (
          <>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={applying}
              className="h-9 min-w-52 flex-1 justify-start truncate font-normal"
              onClick={onPick}
            >
              {file ? file.name : "Choose file…"}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="icon"
              disabled={!fileHandle || applying || staging}
              title="Re-read this file from disk"
              aria-label="Refresh CSV from disk"
              className="h-9 w-9 shrink-0"
              onClick={onRefresh}
            >
              <RefreshCw className="size-3.5" />
            </Button>
          </>
        ) : (
          <Input
            id="member-import-file"
            type="file"
            accept=".csv,text/csv"
            disabled={applying}
            className="h-9 min-w-52 flex-1"
            onChange={(event) => onSelectFile(event.target.files?.[0] ?? null)}
          />
        )}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-9 shrink-0"
          onClick={onDownloadTemplate}
        >
          <Download className="mr-1.5 size-3.5" />
          Template
        </Button>
      </div>
      <p className="text-xs text-fg-muted">
        Company Code resolves the client. Supported fields: Company Code, Staff_ID, Staff Number,
        Name of Employee, Email Address, Personal Email, Date of Birth (YYYY-MM-DD), Gender, Phone,
        National ID, Passport Number, Status, Relation, and Primary Staff ID. Job Title, Job
        Classification, Skill, Department, Unit and Contract type are also imported when present.
        Any other column is ignored; files are limited to 10 MB.
      </p>

      {staging ? <p className="text-xs text-fg-muted">Staging rows on the server…</p> : null}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </>
  )
}

function ImportPreview({
  batch,
  rows,
  queued,
  applying,
  applied,
  showEmployment,
  updateDecision,
}: {
  batch: MemberImportBatch | null
  rows: MemberImportRow[]
  queued: MemberImportRow[]
  applying: boolean
  applied: boolean
  showEmployment: boolean
  updateDecision: (row: MemberImportRow, decision: MemberImportRowDecision) => void
}) {
  if (!batch) return null
  return (
    <div className="space-y-3 border-t border-fg/10 pt-4">
      <ImportSummary rows={rows} queued={queued.length} applying={applying} applied={applied} />
      <div className="max-h-[28rem] overflow-auto rounded-sm border border-fg/10">
        <Table className="text-left text-xs">
          <TableHeader className="sticky top-0 bg-surface text-fg-muted">
            <TableRow className="border-fg/10">
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">#</TableHead>
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Name</TableHead>
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Staff ID</TableHead>
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Staff no.</TableHead>
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Client</TableHead>
              {showEmployment
                ? EMPLOYMENT_COLUMNS.map((column) => (
                    <TableHead key={column.key} className="h-auto px-2 py-1 text-xs font-medium">
                      {column.label}
                    </TableHead>
                  ))
                : null}
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Decision</TableHead>
              <TableHead className="h-auto px-2 py-1 text-xs font-medium">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <ImportRowLine
                key={row.id}
                row={row}
                applying={applying}
                applied={applied}
                showEmployment={showEmployment}
                onDecision={updateDecision}
              />
            ))}
          </TableBody>
        </Table>
      </div>
      {rows.some((row) => row.outcome === "Invalid" || row.outcome === "Failed") ? (
        <Button
          type="button"
          variant="link"
          size="sm"
          className="h-auto gap-1 px-0 text-xs"
          onClick={() => downloadIssues(rows)}
        >
          <Download className="size-3" />
          Download issue report
        </Button>
      ) : null}
    </div>
  )
}

function ImportFooter({
  batch,
  queued,
  staging,
  applying,
  applied,
  onOpenChange,
  applyImport,
}: {
  batch: MemberImportBatch | null
  queued: MemberImportRow[]
  staging: boolean
  applying: boolean
  applied: boolean
  onOpenChange: (open: boolean) => void
  applyImport: () => void
}) {
  return (
    <SheetFooter className="shrink-0 justify-end gap-2 border-t border-fg/10 bg-surface px-6 py-3">
      <Button
        type="button"
        variant="outline"
        disabled={applying}
        onClick={() => onOpenChange(false)}
      >
        {applied ? "Done" : "Close"}
      </Button>
      <Button
        type="button"
        disabled={!batch || staging || applying || applied || queued.length === 0}
        onClick={() => void applyImport()}
      >
        <FileInput className="mr-1.5 size-4" />
        {applying ? "Applying…" : `Import ${queued.length} rows`}
      </Button>
    </SheetFooter>
  )
}

export function MemberImportDialog({ open, onOpenChange, onImported }: MemberImportDialogProps) {
  const toast = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [fileHandle, setFileHandle] = useState<FileSystemFileHandle | null>(null)
  const [batch, setBatch] = useState<MemberImportBatch | null>(null)
  const [rows, setRows] = useState<MemberImportRow[]>([])
  const [staging, setStaging] = useState(false)
  const [applying, setApplying] = useState(false)
  const [applied, setApplied] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) return
    setFile(null)
    setFileHandle(null)
    setBatch(null)
    setRows([])
    setStaging(false)
    setApplying(false)
    setApplied(false)
    setError(null)
  }, [open])

  const queued = rows.filter(isQueued)
  const showEmployment = rows.some((row) => row.employment)

  const selectFile = (selected: File | null, handle: FileSystemFileHandle | null = null) => {
    setFile(selected)
    setFileHandle(handle)
    setBatch(null)
    setRows([])
    setApplied(false)
    setError(null)
    if (!selected) return
    setStaging(true)
    void membersApi
      .stageImport(selected)
      .then(async (staged) => {
        setBatch(staged)
        setRows(await fetchAllRows(staged.id))
      })
      .catch((cause) => setError(normalizeErrorMessage(cause, "Could not stage the CSV")))
      .finally(() => setStaging(false))
  }

  const pickFile = async () => {
    if (!window.showOpenFilePicker) return
    try {
      const [handle] = await window.showOpenFilePicker({
        types: [{ description: "CSV", accept: { "text/csv": [".csv"] } }],
        excludeAcceptAllOption: false,
        multiple: false,
      })
      selectFile(await handle.getFile(), handle)
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return
      setError(normalizeErrorMessage(cause, "Could not open the CSV file"))
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
      setError(normalizeErrorMessage(cause, "Could not refresh the CSV file"))
    }
  }

  const updateDecision = (row: MemberImportRow, decision: MemberImportRowDecision) => {
    if (!batch) return
    setRows((current) => current.map((r) => (r.id === row.id ? { ...r, decision } : r)))
    void membersApi.setImportRowDecision(batch.id, row.id, decision).catch((cause) => {
      toast.showError(normalizeErrorMessage(cause, "Could not update the row"))
      setRows((current) => current.map((r) => (r.id === row.id ? row : r)))
    })
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

  const applyImport = async () => {
    if (!batch) return
    setApplying(true)
    setError(null)
    try {
      const result = await membersApi.applyImport(batch.id)
      setRows(await fetchAllRows(batch.id))
      setApplied(true)
      if (result.imported > 0) onImported()
      const attention = result.failed + result.not_importable
      if (attention === 0) toast.showSuccess(`${result.imported} member rows imported`)
      else toast.showError(`${attention} row${attention === 1 ? "" : "s"} need attention`)
    } catch (cause) {
      setError(normalizeErrorMessage(cause, "Could not apply the import"))
    } finally {
      setApplying(false)
    }
  }

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
            Upload a roster, review every row, then apply. Staff_ID is the stable identity key;
            existing members are never overwritten.
          </SheetDescription>
        </SheetHeader>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-5">
          <ImportControls
            file={file}
            fileHandle={fileHandle}
            applying={applying}
            staging={staging}
            error={error}
            onPick={() => void pickFile()}
            onRefresh={() => void refreshFile()}
            onSelectFile={selectFile}
            onDownloadTemplate={() => void downloadTemplate()}
          />
          <ImportPreview
            batch={batch}
            rows={rows}
            queued={queued}
            applying={applying}
            applied={applied}
            showEmployment={showEmployment}
            updateDecision={updateDecision}
          />
        </div>

        <ImportFooter
          batch={batch}
          queued={queued}
          staging={staging}
          applying={applying}
          applied={applied}
          onOpenChange={onOpenChange}
          applyImport={() => void applyImport()}
        />
      </SheetContent>
    </Sheet>
  )
}

function ImportSummary({
  rows,
  queued,
  applying,
  applied,
}: {
  rows: MemberImportRow[]
  queued: number
  applying: boolean
  applied: boolean
}) {
  if (applying) return <p className="text-sm text-fg-muted">Applying the import…</p>
  if (applied) {
    const imported = rows.filter((row) => row.imported_member_id).length
    const failed = rows.filter((row) => !row.imported_member_id && row.outcome === "Failed").length
    return (
      <p className="text-sm">
        <strong>{imported}</strong> imported · <strong>{rows.length - imported - failed}</strong>{" "}
        skipped · <strong>{failed}</strong> failed
      </p>
    )
  }
  const invalid = rows.filter((row) => row.outcome === "Invalid").length
  return (
    <p className="text-sm">
      <strong>{rows.length}</strong> rows checked · <strong>{queued}</strong> ready ·{" "}
      <strong>{rows.length - queued - invalid}</strong> skipped · <strong>{invalid}</strong> errors
    </p>
  )
}

/** Optional roster columns, rendered only when a file carries some. */
const EMPLOYMENT_COLUMNS = [
  { key: "job_title", label: "Job title" },
  { key: "job_classification", label: "Classification" },
  { key: "skill", label: "Skill" },
  { key: "department", label: "Department" },
  { key: "unit", label: "Unit" },
  { key: "employment_type", label: "Contract" },
] as const

function EmploymentCells({ row }: { row: MemberImportRow }) {
  return (
    <>
      {EMPLOYMENT_COLUMNS.map((column) => (
        <TableCell key={column.key} className="max-w-36 truncate px-2 py-1 text-xs text-fg-muted">
          {row.employment?.[column.key] ?? "-"}
        </TableCell>
      ))}
    </>
  )
}

function DecisionCell({
  row,
  applying,
  applied,
  onDecision,
}: {
  row: MemberImportRow
  applying: boolean
  applied: boolean
  onDecision: (row: MemberImportRow, decision: MemberImportRowDecision) => void
}) {
  if (row.outcome !== "New" || applied) {
    return (
      <TableCell className="px-2 py-1 text-xs">
        <span className="text-fg-muted">-</span>
      </TableCell>
    )
  }
  return (
    <TableCell className="px-2 py-1 text-xs">
      <Select
        value={row.decision}
        disabled={applying}
        onValueChange={(value) => onDecision(row, value as MemberImportRowDecision)}
      >
        <SelectTrigger
          aria-label={`Decision for row ${row.row_number}`}
          className="h-7 rounded-sm border-fg/15 bg-bg px-2 text-xs text-fg"
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="import">Import</SelectItem>
          <SelectItem value="skip">Skip</SelectItem>
        </SelectContent>
      </Select>
    </TableCell>
  )
}

function ImportRowLine({
  row,
  applying,
  applied,
  showEmployment,
  onDecision,
}: {
  row: MemberImportRow
  applying: boolean
  applied: boolean
  showEmployment: boolean
  onDecision: (row: MemberImportRow, decision: MemberImportRowDecision) => void
}) {
  const status = rowStatus(row, applied)
  return (
    <TableRow className="border-fg/8">
      <TableCell className="px-2 py-1 text-xs text-fg-muted">{row.row_number}</TableCell>
      <TableCell className="max-w-44 truncate px-2 py-1 text-xs text-fg">
        {row.display_label ?? "Unnamed"}
      </TableCell>
      <TableCell className="px-2 py-1 text-xs text-fg-muted">
        {row.import_source_id ?? "-"}
      </TableCell>
      <TableCell className="px-2 py-1 text-xs text-fg-muted">{row.staff_number ?? "-"}</TableCell>
      <TableCell className="max-w-36 truncate px-2 py-1 text-xs text-fg-muted">
        {row.client_name ?? row.client_code ?? "Unresolved"}
      </TableCell>
      {showEmployment ? <EmploymentCells row={row} /> : null}
      <DecisionCell row={row} applying={applying} applied={applied} onDecision={onDecision} />
      <TableCell className={`max-w-52 truncate px-2 py-1 text-xs ${TONE_CLASS[status.tone]}`}>
        {status.label}
      </TableCell>
    </TableRow>
  )
}
