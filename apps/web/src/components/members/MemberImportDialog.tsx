import { useEffect, useState } from "react"

import { Download, FileInput } from "lucide-react"

import { type MemberImportResult,membersApi } from "@/api/endpoints/members"
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

export function MemberImportDialog({ open, onOpenChange, onImported }: MemberImportDialogProps) {
  const toast = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<MemberImportResult | null>(null)
  const [result, setResult] = useState<MemberImportResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      setFile(null)
      setPreview(null)
      setResult(null)
      setLoading(false)
      setError(null)
    }
  }, [open])

  const selectFile = (selected: File | null) => {
    setFile(selected)
    setPreview(null)
    setResult(null)
    setError(null)
    if (!selected) return
    setLoading(true)
    void membersApi
      .importRoster(selected, true)
      .then(setPreview)
      .catch((cause) => setError(normalizeErrorMessage(cause, "Could not preview CSV")))
      .finally(() => setLoading(false))
  }

  const importFile = async () => {
    if (!file || !preview) return
    setLoading(true)
    try {
      const imported = await membersApi.importRoster(file, false)
      setResult(imported)
      if (imported.imported > 0) onImported()
      if (imported.failed > 0) toast.showError("Import needs attention. Review the row errors.")
      else toast.showSuccess(`${imported.imported} member rows imported`)
    } catch (cause) {
      toast.showError(normalizeErrorMessage(cause, "Could not import members"))
    } finally {
      setLoading(false)
    }
  }

  const rows = result?.rows ?? preview?.rows ?? []
  const failed = result?.failed ?? preview?.failed ?? 0

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="flex h-full w-full flex-col gap-0 rounded-none border-l border-fg/15 bg-bg p-0 sm:max-w-2xl"
      >
        <SheetHeader className="shrink-0 border-b border-fg/10 px-6 py-5 pr-14 text-left">
          <SheetTitle className="text-base text-fg">Import members</SheetTitle>
          <SheetDescription className="text-xs leading-relaxed text-fg/60">
            Upload a roster, review every row, then confirm. Staff_ID must be a stable client identifier.
          </SheetDescription>
        </SheetHeader>
        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <Label htmlFor="member-import-file">CSV file</Label>
              <Input
                id="member-import-file"
                className="mt-2"
                type="file"
                accept=".csv,text/csv"
                onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
              />
            </div>
            <Button type="button" variant="outline" size="sm" onClick={downloadTemplate}>
              <Download className="mr-1.5 size-3.5" />
              Template
            </Button>
          </div>
          <p className="text-xs text-fg-muted">
            Company Code resolves the client. Staff Number is not used for identity matching.
          </p>
          {loading && !preview ? <p className="text-xs text-fg-muted">Checking rows…</p> : null}
          {error ? <p className="text-xs text-destructive">{error}</p> : null}
          {preview ? (
            <div className="space-y-3 border-t border-fg/10 pt-4">
              <p className="text-sm">
                <strong>{preview.rows.length}</strong> rows checked · <strong>{preview.failed}</strong> errors
              </p>
              <div className="max-h-[30rem] overflow-auto rounded-sm border border-fg/10">
                <Table className="text-left text-xs">
                  <TableHeader className="sticky top-0 bg-surface text-fg-muted">
                    <TableRow>
                      <TableHead>Row</TableHead>
                      <TableHead>Member</TableHead>
                      <TableHead>Client</TableHead>
                      <TableHead>Result</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((row) => (
                      <TableRow key={row.row} className="border-fg/8">
                        <TableCell>{row.row}</TableCell>
                        <TableCell>
                          <div>{row.display_label ?? "Unnamed"}</div>
                          <div className="text-fg-muted">
                            {row.employer_member_id ?? "No Staff_ID"}
                            {row.staff_number ? ` · ${row.staff_number}` : ""}
                          </div>
                        </TableCell>
                        <TableCell>{row.client_name ?? row.client_code ?? "Unresolved"}</TableCell>
                        <TableCell className={row.state === "invalid" ? "text-destructive" : "text-primary"}>
                          {row.message ?? (row.state === "invalid" ? "Invalid" : "Ready")}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          ) : null}
          {result ? (
            <p className="border-t border-fg/10 pt-4 text-sm">
              <strong>{result.imported}</strong> imported · <strong>{result.failed}</strong> errors
            </p>
          ) : null}
        </div>
        <SheetFooter className="shrink-0 justify-end gap-2 border-t border-fg/10 bg-surface px-6 py-3">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button type="button" disabled={!file || !preview || failed > 0 || loading} onClick={() => void importFile()}>
            <FileInput className="mr-1.5 size-4" />
            {loading ? "Importing…" : `Confirm import${preview ? ` (${preview.imported})` : ""}`}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
