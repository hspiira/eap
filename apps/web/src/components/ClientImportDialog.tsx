import { useEffect, useState } from "react"

import { Download, FileInput } from "lucide-react"

import { type ClientImportResult, clientsApi } from "@/api/endpoints/clients"
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

interface ClientImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onImported: () => void
}

interface ImportPreview {
  rows: Array<{ line: number; name: string; code: string; contact: string }>
  totalRows: number
  uniqueNames: number
}

function parseCsv(text: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let value = ""
  let quoted = false

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index]
    const next = text[index + 1]
    if (character === '"') {
      if (quoted && next === '"') {
        value += '"'
        index += 1
      } else {
        quoted = !quoted
      }
    } else if (character === "," && !quoted) {
      row.push(value)
      value = ""
    } else if ((character === "\n" || character === "\r") && !quoted) {
      if (character === "\r" && next === "\n") index += 1
      row.push(value)
      if (row.some((cell) => cell.trim())) rows.push(row)
      row = []
      value = ""
    } else {
      value += character
    }
  }

  row.push(value)
  if (row.some((cell) => cell.trim())) rows.push(row)
  return rows
}

function headerKey(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "")
}

function firstHeaderIndex(headers: string[], names: string[]): number | undefined {
  const index = names.map((name) => headers.indexOf(name)).find((value) => value >= 0)
  return index === undefined ? undefined : index
}

function makePreview(text: string): ImportPreview {
  const records = parseCsv(text)
  if (records.length < 2) throw new Error("CSV must contain a header and at least one data row")

  const headers = records[0].map(headerKey)
  const nameIndex = firstHeaderIndex(headers, [
    "name",
    "client_name",
    "company_name",
    "canonical_name",
    "company",
    "canonical_list",
    "og_company",
  ])
  if (nameIndex === undefined) {
    throw new Error("CSV must include a name column, such as name or Company Name")
  }

  const codeIndex = firstHeaderIndex(headers, ["code", "client_code"])
  const contactIndexes = ["email", "phone"]
    .map((name) => headers.indexOf(name))
    .filter((index) => index >= 0)
  const dataRows = records.slice(1).filter((row) => row[nameIndex]?.trim())
  const names = new Set(dataRows.map((row) => row[nameIndex].trim().toLowerCase()))

  return {
    totalRows: dataRows.length,
    uniqueNames: names.size,
    rows: dataRows.slice(0, 12).map((row, index) => ({
      line: index + 2,
      name: row[nameIndex].trim(),
      code: codeIndex === undefined ? "Auto" : row[codeIndex]?.trim() || "Auto",
      contact: contactIndexes
        .map((contactIndex) => row[contactIndex]?.trim())
        .filter(Boolean)
        .join(" · "),
    })),
  }
}

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

export function ClientImportDialog({ open, onOpenChange, onImported }: ClientImportDialogProps) {
  const toast = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ClientImportResult | null>(null)

  useEffect(() => {
    if (!open) {
      setFile(null)
      setPreview(null)
      setPreviewError(null)
      setPreviewLoading(false)
      setResult(null)
      setLoading(false)
    }
  }, [open])

  const selectFile = (selected: File | null) => {
    setFile(selected)
    setPreview(null)
    setPreviewError(null)
    setResult(null)
    if (!selected) return

    setPreviewLoading(true)
    void selected
      .text()
      .then((text) => setPreview(makePreview(text)))
      .catch((error) =>
        setPreviewError(error instanceof Error ? error.message : "Could not preview CSV"),
      )
      .finally(() => setPreviewLoading(false))
  }

  const importFile = async () => {
    if (!file || !preview) return
    setLoading(true)
    try {
      const imported = await clientsApi.importCsv(file)
      setResult(imported)
      if (imported.imported > 0) onImported()
      if (imported.failed > 0) {
        toast.showError("Import needs attention. No clients were created.")
      } else {
        toast.showSuccess(
          `${imported.imported} client${imported.imported === 1 ? "" : "s"} imported`,
        )
      }
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not import clients"))
    } finally {
      setLoading(false)
    }
  }

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
            Review the file before adding clients. Missing codes are generated automatically.
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
              Company Name is supported for your sample; repeated names are skipped.
            </p>
          </div>

          {previewLoading ? <p className="text-xs text-fg-muted">Reading preview…</p> : null}
          {previewError ? <p className="text-xs text-destructive">{previewError}</p> : null}
          {preview ? (
            <div className="space-y-2 border-t border-fg/10 pt-4">
              <p className="text-sm">
                <strong>{preview.totalRows}</strong> rows · <strong>{preview.uniqueNames}</strong>{" "}
                unique names
                {preview.totalRows !== preview.uniqueNames ? " · duplicates will be skipped" : ""}
              </p>
              <div className="max-h-[28rem] overflow-auto rounded-sm border border-fg/10">
                <Table className="text-left text-xs">
                  <TableHeader className="sticky top-0 bg-surface text-fg-muted">
                    <TableRow>
                      <TableHead className="h-auto px-2 py-1.5 font-medium">Row</TableHead>
                      <TableHead className="h-auto px-2 py-1.5 font-medium">Client name</TableHead>
                      <TableHead className="h-auto px-2 py-1.5 font-medium">Code</TableHead>
                      <TableHead className="h-auto px-2 py-1.5 font-medium">Contact</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.rows.map((row) => (
                      <TableRow key={row.line} className="border-fg/8">
                        <TableCell className="px-2 py-1.5 text-fg-muted">{row.line}</TableCell>
                        <TableCell className="px-2 py-1.5 text-fg">{row.name}</TableCell>
                        <TableCell className="px-2 py-1.5 text-fg-muted">
                          {row.code}
                        </TableCell>
                        <TableCell className="px-2 py-1.5 text-fg-muted">
                          {row.contact || "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              {preview.totalRows > preview.rows.length ? (
                <p className="text-xs text-fg-muted">
                  Showing the first {preview.rows.length} rows.
                </p>
              ) : null}
            </div>
          ) : null}

          {result ? (
            <div className="space-y-2 border-t border-fg/10 pt-4 text-sm">
              <p>
                <strong>{result.imported}</strong> imported · <strong>{result.skipped}</strong>{" "}
                skipped · <strong>{result.failed}</strong> needing attention
              </p>
              {result.issues.length > 0 ? (
                <>
                  <ul className="max-h-32 overflow-auto rounded-sm bg-fg/5 p-2 text-xs text-fg-muted">
                  {result.issues.slice(0, 20).map((issue, index) => (
                    <li key={`${issue.row}-${issue.field}-${index}`}>
                      {issue.severity === "warning" ? "Review" : "Row"} {issue.row}
                      {issue.field ? ` · ${issue.field}` : ""}: {issue.message}
                    </li>
                  ))}
                  {result.issues.length > 20 ? (
                    <li>…and {result.issues.length - 20} more</li>
                  ) : null}
                  </ul>
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
                </>
              ) : null}
            </div>
          ) : null}
        </div>

        <SheetFooter className="shrink-0 justify-end gap-2 border-t border-fg/10 bg-surface px-6 py-3">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button
            type="button"
            disabled={!file || !preview || previewError !== null || previewLoading || loading}
            onClick={() => void importFile()}
          >
            <FileInput className="mr-1.5 size-4" />
            {loading ? "Importing…" : `Confirm import${preview ? ` (${preview.uniqueNames})` : ""}`}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
