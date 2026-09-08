import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Check, CircleDashed, X } from "lucide-react"

import { type EngagementDocument, providersApi } from "@/api/endpoints/providers"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/contexts/ToastContext"
import { useCurrentRole } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import { EngagementDocumentKind, EngagementDocumentState, TenantRole } from "@/types/enums"

/** The order an engagement is assembled in, not alphabetical. */
const KIND_ORDER: EngagementDocumentKind[] = [
  EngagementDocumentKind.CONTRACT,
  EngagementDocumentKind.MOA,
  EngagementDocumentKind.KYC,
  EngagementDocumentKind.CERTIFICATE_OF_REGISTRATION,
  EngagementDocumentKind.UCA_LICENCE,
  EngagementDocumentKind.DECLARATION_FORM,
  EngagementDocumentKind.LEAD_CONSULTANT_CV,
]

const KIND_LABELS: Record<EngagementDocumentKind, string> = {
  [EngagementDocumentKind.CONTRACT]: "Contract",
  [EngagementDocumentKind.MOA]: "Memorandum of agreement",
  [EngagementDocumentKind.KYC]: "KYC",
  [EngagementDocumentKind.CERTIFICATE_OF_REGISTRATION]: "Certificate of registration",
  [EngagementDocumentKind.UCA_LICENCE]: "UCA licence",
  [EngagementDocumentKind.DECLARATION_FORM]: "Declaration form",
  [EngagementDocumentKind.LEAD_CONSULTANT_CV]: "Lead consultant CV",
}

const STATE_ICON = {
  [EngagementDocumentState.PRESENT]: { Icon: Check, className: "text-success-fg" },
  [EngagementDocumentState.MISSING]: { Icon: X, className: "text-danger-fg" },
  [EngagementDocumentState.OPEN]: { Icon: CircleDashed, className: "text-warning-fg" },
}

function StateMark({ state }: { state?: EngagementDocumentState }) {
  if (!state) {
    return <CircleDashed aria-hidden className="size-3.5 shrink-0 text-fg-subtle" />
  }
  const { Icon, className } = STATE_ICON[state]
  return <Icon aria-hidden className={`size-3.5 shrink-0 ${className}`} />
}

/**
 * The seven documents an engagement requires, one row each. An entry that has
 * never been recorded is not the same as one recorded Missing, so an
 * unrecorded row says so rather than presuming the answer.
 */
export function ProviderEngagementDocumentsCard({ providerId }: { providerId: string }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const [editing, setEditing] = useState<EngagementDocumentKind | null>(null)
  const [state, setState] = useState<EngagementDocumentState>(EngagementDocumentState.PRESENT)
  const [note, setNote] = useState("")
  const [saving, setSaving] = useState(false)

  const query = useQuery({
    queryKey: ["providers", providerId, "engagement-documents"],
    queryFn: () => providersApi.listEngagementDocuments(providerId),
  })

  const byKind = new Map<string, EngagementDocument>(
    (query.data ?? []).map((entry) => [entry.document_kind, entry]),
  )
  const held = KIND_ORDER.filter(
    (kind) => byKind.get(kind)?.state === EngagementDocumentState.PRESENT,
  ).length

  const open = (kind: EngagementDocumentKind) => {
    const current = byKind.get(kind)
    setState(current?.state ?? EngagementDocumentState.PRESENT)
    setNote(current?.note ?? "")
    setEditing(kind)
  }

  const save = async () => {
    if (!editing) return
    setSaving(true)
    try {
      await providersApi.upsertEngagementDocument(providerId, editing, { state, note: note || null })
      await queryClient.invalidateQueries({
        queryKey: ["providers", providerId, "engagement-documents"],
      })
      toast.showSuccess("Document checklist updated")
      setEditing(null)
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not update the checklist"))
    } finally {
      setSaving(false)
    }
  }

  return (
    <DetailCard title="Engagement documents">
      {query.isPending ? (
        <p className="text-xs text-fg-muted">Loading checklist…</p>
      ) : query.isError ? (
        <p className="text-xs text-danger-fg" role="alert">
          Could not load the document checklist.
        </p>
      ) : (
        <>
          <p className="mb-3 text-xs text-fg-muted">
            {held} of {KIND_ORDER.length} held.
          </p>
          <ul className="space-y-1">
            {KIND_ORDER.map((kind) => {
              const entry = byKind.get(kind)
              return (
                <li key={kind} className="flex items-center gap-2 py-0.5">
                  <StateMark state={entry?.state} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-xs text-fg">{KIND_LABELS[kind]}</span>
                    {entry?.note ? (
                      <span className="block truncate text-[11px] text-fg-muted">{entry.note}</span>
                    ) : null}
                  </span>
                  <span className="shrink-0 text-[11px] text-fg-muted">
                    {entry ? entry.state : "Not recorded"}
                  </span>
                  {isAdmin ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-6 shrink-0 rounded-sm px-1.5 text-[11px]"
                      onClick={() => open(kind)}
                    >
                      Record
                    </Button>
                  ) : null}
                </li>
              )
            })}
          </ul>
        </>
      )}

      <Dialog
        open={editing !== null}
        onOpenChange={(next) => {
          if (!next) setEditing(null)
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editing ? `Record ${KIND_LABELS[editing]}` : "Record document"}
            </DialogTitle>
            <DialogDescription>
              Whether the document is held. Recorded against the practitioner and audited.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
          <label className="block space-y-1">
            <span className="text-xs font-medium text-fg">State</span>
            <Select
              value={state}
              onValueChange={(value) => setState(value as EngagementDocumentState)}
            >
              <SelectTrigger className="h-8 rounded-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.values(EngagementDocumentState).map((value) => (
                  <SelectItem key={value} value={value}>
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>
            <label className="block space-y-1">
              <span className="text-xs font-medium text-fg">Note</span>
              <Input
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="Optional"
                className="h-8 rounded-none"
              />
            </label>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setEditing(null)}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button type="button" size="sm" onClick={() => void save()} disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DetailCard>
  )
}
