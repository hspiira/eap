import { useEffect, useState } from "react"

import { Download, FileInput } from "lucide-react"

import { type MemberImportResult, membersApi } from "@/api/endpoints/members"
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

interface MemberImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onImported: () => void
}

const TEMPLATE = [
  "Company Code",
  "Staff_ID",
  "Name of Employee",
  "Email Address",
  "Gender",
  "Status",
  "Relation",
  "Primary Staff ID",
].join(",")

function downloadTemplate() {
  const url = URL.createObjectURL(new Blob([`${TEMPLATE}\n`], { type: "text/csv;charset=utf-8" }))
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = "members-template.csv"
  anchor.click()
  URL.revokeObjectURL(url)
}

function downloadIssues(issues: MemberImportResult["issues"]): void {
  const escape = (value: string) => `"${value.replaceAll('"', '""')}"`
  const csv = [
    ["row", "field", "message"],
    ...issues.map((issue) => [String(issue.row), issue.field ?? "", issue.message]),
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

function decisionsFor(rows: MemberImportResult["rows"]): Record<number, "import" | "skip"> {
  return Object.fromEntries(rows.map((row) => [row.row, row.default_action]))
}

function stateLabel(state: string, message?: string | null): string {
  if (message) return message
  if (state === "duplicate") return "Existing · skipped"
  if (state === "skipped") return "Skipped"
  if (state === "invalid") return "Invalid"
  return "Ready to import"
}

export function MemberImportDialog({ open, onOpenChange, onImported }: MemberImportDialogProps) {
  const toast = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<MemberImportResult | null>(null)
  const [result, setResult] = useState<MemberImportResult | null>(null)
  const [decisions, setDecisions] = useState<Record<number, "import" | "skip">>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      setFile(null)
      setPreview(null)
      setResult(null)
      setDecisions({})
      setLoading(false)
      setError(null)
    }
  }, [open])

  const selectFile = (selected: File | null) => {
    setFile(selected)
    setPreview(null)
    setResult(null)
    setDecisions({})
    setError(null)
    if (!selected) return
    setLoading(true)
    void membersApi
      .importRoster(selected, true)
      .then((serverPreview) => {
        setPreview(serverPreview)
        setDecisions(decisionsFor(serverPreview.rows))
      })
      .catch((cause) => setError(normalizeErrorMessage(cause, "Could not preview CSV")))
      .finally(() => setLoading(false))
  }

  const updateDecision = (row: number, value: "import" | "skip") => {
    setDecisions((current) => ({ ...current, [row]: value }))
  }

  const importFile = async () => {
    if (!file || !preview) return
    setLoading(true)
    try {
      const imported = await membersApi.importRoster(file, false, decisions)
      setResult(imported)
      if (imported.imported > 0) onImported()
      if (imported.failed > 0) toast.showError("Import needs attention. Download the issue report.")
      else toast.showSuccess(`${imported.imported} member rows imported`)
    } catch (cause) {
      toast.showError(normalizeErrorMessage(cause, "Could not import members"))
    } finally {
      setLoading(false)
    }
  }

  const rows = result?.rows ?? preview?.rows ?? []
  const issues = result?.issues ?? preview?.issues ?? []
  const canConfirm = Boolean(file && preview && preview.failed === 0 && !loading)
  const selectedCount = rows.filter(
    (row) => row.state !== "duplicate" && row.state !== "invalid" && decisions[row.row] !== "skip",
  ).length

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="flex h-full w-full flex-col gap-0 rounded-none border-l border-fg/15 bg-bg p-0 shadow-lg sm:max-w-2xl lg:max-w-3xl"
        onPointerDownOutside={(event) => event.preventDefault()}
        onEscapeKeyDown={(event) => event.preventDefault()}
      >
        <SheetHeader className="shrink-0 border-b border-fg/10 px-6 py-5 pr-14 text-left">
          <SheetTitle className="text-base text-fg">Import members</SheetTitle>
          <SheetDescription className="text-xs leading-relaxed text-fg/60">
            Upload a roster, review every row, then confirm. Staff_ID is the stable identity key;
            existing members are never overwritten.
          </SheetDescription>
        </SheetHeader>

        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-5">
          <div className="space-y-2">
            <div className="flex items-end justify-between gap-3">
              <Label htmlFor="member-import-file">CSV file</Label>
              <Button type="button" variant="outline" size="sm" onClick={downloadTemplate}>
                <Download className="mr-1.5 size-3.5" />
                Template
              </Button>
            </div>
            <Input
              id="member-import-file"
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
            />
            <p className="text-xs text-fg-muted">
              Company Code resolves the client. Staff Number is retained for reference, never
              identity matching.
            </p>
          </div>

          {loading && !preview ? (
            <p className="text-xs text-fg-muted">Checking rows on the server…</p>
          ) : null}
          {error ? <p className="text-xs text-destructive">{error}</p> : null}

          {preview ? (
            <div className="space-y-3 border-t border-fg/10 pt-4">
              <p className="text-sm">
                <strong>{preview.rows.length}</strong> rows checked ·{" "}
                <strong>{preview.imported}</strong> ready · <strong>{preview.skipped}</strong>{" "}
                skipped · <strong>{preview.failed}</strong> errors
              </p>
              <div className="max-h-[30rem] overflow-auto rounded-sm border border-fg/10">
                <Table className="text-left text-xs">
                  <TableHeader className="sticky top-0 bg-surface text-fg-muted">
                    <TableRow>
                      <TableHead className="h-auto px-2 py-1.5 font-medium">Row</TableHead>
                      <TableHead className="h-auto px-2 py-1.5 font-medium">Member</TableHead>
                      <TableHead className="h-auto px-2 py-1.5 font-medium">Client</TableHead>
                      <TableHead className="h-auto px-2 py-1.5 font-medium">Decision</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((row) => {
                      const decision = decisions[row.row] ?? row.default_action
                      const duplicate = row.state === "duplicate"
                      return (
                        <TableRow key={row.row} className="border-fg/8">
                          <TableCell className="px-2 py-1.5 text-fg-muted">{row.row}</TableCell>
                          <TableCell className="max-w-56 px-2 py-1.5 text-fg">
                            <div>{row.display_label ?? "Unnamed"}</div>
                            <div className="text-fg-muted">
                              {row.employer_member_id ?? "No Staff_ID"}
                              {row.staff_number ? ` · ${row.staff_number}` : ""}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-40 px-2 py-1.5 text-fg-muted">
                            {row.client_name ?? row.client_code ?? "Unresolved"}
                          </TableCell>
                          <TableCell className="px-2 py-1.5">
                            {row.state === "invalid" ? (
                              <span className="text-destructive">
                                {stateLabel(row.state, row.message)}
                              </span>
                            ) : duplicate ? (
                              <span className="text-fg-muted">
                                {stateLabel(row.state, row.message)}
                              </span>
                            ) : (
                              <Select
                                value={decision}
                                onValueChange={(value) =>
                                  updateDecision(row.row, value as "import" | "skip")
                                }
                              >
                                <SelectTrigger
                                  aria-label={`Decision for row ${row.row}`}
                                  className="h-8 rounded-sm border-fg/15 bg-bg px-2 text-xs text-fg"
                                >
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="import">Import</SelectItem>
                                  <SelectItem value="skip">Skip</SelectItem>
                                </SelectContent>
                              </Select>
                            )}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
              {issues.length > 0 ? (
                <Button
                  type="button"
                  variant="link"
                  size="sm"
                  className="h-auto gap-1 px-0 text-xs"
                  onClick={() => downloadIssues(issues)}
                >
                  <Download className="size-3" />
                  Download issue report
                </Button>
              ) : null}
            </div>
          ) : null}

          {result ? (
            <div className="space-y-2 border-t border-fg/10 pt-4 text-sm">
              <p>
                <strong>{result.imported}</strong> imported · <strong>{result.skipped}</strong>{" "}
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
                  Download server issue report
                </Button>
              ) : null}
            </div>
          ) : null}
        </div>

        <SheetFooter className="shrink-0 justify-end gap-2 border-t border-fg/10 bg-surface px-6 py-3">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button type="button" disabled={!canConfirm} onClick={() => void importFile()}>
            <FileInput className="mr-1.5 size-4" />
            {loading ? "Importing…" : `Confirm import${preview ? ` (${selectedCount})` : ""}`}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
