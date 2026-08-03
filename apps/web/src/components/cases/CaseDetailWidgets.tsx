import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { HeartPulse, Lock, ShieldCheck } from "lucide-react"

import { usersApi } from "@/api/endpoints/users"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  RailSection,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { FormField } from "@/components/common/FormField"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import type { Case, ClinicalNote, ClinicalNoteBody } from "@/types/entities"
import { AccessScope, CaseClosureReason, CaseStatus, ClinicalNoteType } from "@/types/enums"
import {
  CaseClosureReasonLabel,
  CasePresentingProblemLabel,
  CaseReferralSourceLabel,
  ClinicalNoteTypeLabel,
} from "@/utils/caseLabels"

export function Hero({ caseData }: { caseData: Case }) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <HeartPulse className="size-4" />
      </span>
      <h1 className="shrink truncate font-mono text-sm font-semibold leading-tight text-fg">
        {caseData.clinical_subject_id}
      </h1>
      <span className="text-xs text-fg/65">
        {CasePresentingProblemLabel[caseData.presenting_problem]}
      </span>
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={caseData.status} />
    </div>
  )
}

export function OverviewPanel({ caseData }: { caseData: Case }) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <DetailCard title="Referral">
        <DetailGrid>
          <DetailRow
            label="Presenting problem"
            value={CasePresentingProblemLabel[caseData.presenting_problem]}
          />
          <DetailRow
            label="Referral source"
            value={CaseReferralSourceLabel[caseData.referral_source]}
          />
          <DetailRow label="Referral notes" value={caseData.referral_notes} fullWidth />
        </DetailGrid>
      </DetailCard>

      <DetailCard title="Timeline">
        <DetailGrid>
          <DetailRow label="Opened" value={new Date(caseData.opened_at).toLocaleString()} />
          <DetailRow
            label="Closed"
            value={caseData.closed_at ? new Date(caseData.closed_at).toLocaleString() : null}
          />
          <DetailRow
            label="Closure reason"
            value={
              caseData.closure_reason
                ? CaseClosureReasonLabel[caseData.closure_reason]
                : null
            }
          />
        </DetailGrid>
      </DetailCard>

      <DetailCard title="Screeners" phiLabel="PHI · access logged">
        <DetailGrid>
          <DetailRow
            label="Intake screeners administered"
            value={String(caseData.intake_screener_admin_ids.length)}
          />
          <DetailRow
            label="Closure screeners administered"
            value={String(caseData.closure_screener_admin_ids.length)}
          />
        </DetailGrid>
      </DetailCard>
    </div>
  )
}

export function DetailRail({
  caseData,
  onAssignCounsellor,
  onAdvance,
  onClose,
  onReferOut,
  actionLoading,
}: {
  caseData: Case
  onAssignCounsellor: () => void
  onAdvance: () => void
  onClose: () => void
  onReferOut: () => void
  actionLoading: boolean
}) {
  const isTerminal =
    caseData.status === CaseStatus.CLOSED ||
    caseData.status === CaseStatus.REFERRED_OUT ||
    caseData.status === CaseStatus.NO_SHOW_CLOSED
  const { data: counsellor } = useQuery({
    queryKey: ["user", caseData.assigned_counsellor_id ?? ""],
    queryFn: () => usersApi.getById(caseData.assigned_counsellor_id as string),
    enabled: !!caseData.assigned_counsellor_id,
  })

  return (
    <div className="space-y-5">
      <RailSection title="Counsellor">
        {caseData.assigned_counsellor_id ? (
          <p className="text-sm text-fg">{counsellor?.email ?? "Loading…"}</p>
        ) : (
          <p className="text-sm text-fg/55">Unassigned</p>
        )}
        {!isTerminal ? (
          <Button
            size="sm"
            variant="outline"
            className="mt-2 h-7 w-full gap-1.5"
            onClick={onAssignCounsellor}
            disabled={actionLoading}
          >
            {caseData.assigned_counsellor_id ? "Reassign" : "Assign counsellor"}
          </Button>
        ) : null}
      </RailSection>

      {!isTerminal ? (
        <RailSection title="Lifecycle">
          <div className="space-y-2">
            <Button
              size="sm"
              className="h-7 w-full gap-1.5"
              onClick={onAdvance}
              disabled={actionLoading}
            >
              Advance status
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-7 w-full gap-1.5"
              onClick={onClose}
              disabled={actionLoading}
            >
              Close case
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-7 w-full gap-1.5 text-danger"
              onClick={onReferOut}
              disabled={actionLoading}
            >
              Refer out
            </Button>
          </div>
        </RailSection>
      ) : null}
    </div>
  )
}

export function AssignCounsellorDialog({
  open,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (counsellorId: string) => Promise<void>
}) {
  const [counsellorId, setCounsellorId] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const { data } = useQuery({
    queryKey: ["users", "list", "for-counsellor-assign"],
    queryFn: () => usersApi.list({ limit: 100, access_scope: AccessScope.CLINICAL }),
    enabled: open,
  })
  const users = data?.items ?? []

  const handleConfirm = async () => {
    if (!counsellorId) return
    setSubmitting(true)
    try {
      await onConfirm(counsellorId)
      onOpenChange(false)
      setCounsellorId("")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Assign counsellor</DialogTitle>
          <DialogDescription>
            Advancing this case to Active requires a counsellor to already be assigned. Only
            users with Clinical access are shown.
          </DialogDescription>
        </DialogHeader>
        <FormField label="Counsellor" required>
          <Select value={counsellorId} onValueChange={setCounsellorId}>
            <SelectTrigger>
              <SelectValue placeholder="Select…" />
            </SelectTrigger>
            <SelectContent>
              {users.map((u) => (
                <SelectItem key={u.id} value={u.id}>
                  {u.email}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleConfirm} disabled={!counsellorId || submitting}>
            {submitting ? "Assigning…" : "Assign"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

const STATUS_TRANSITIONS: Record<CaseStatus, CaseStatus[]> = {
  [CaseStatus.INTAKE]: [CaseStatus.ASSESSMENT, CaseStatus.NO_SHOW_CLOSED, CaseStatus.REFERRED_OUT],
  [CaseStatus.ASSESSMENT]: [
    CaseStatus.ACTIVE,
    CaseStatus.REFERRED_OUT,
    CaseStatus.NO_SHOW_CLOSED,
    CaseStatus.CLOSED,
  ],
  [CaseStatus.ACTIVE]: [CaseStatus.CLOSED, CaseStatus.REFERRED_OUT, CaseStatus.NO_SHOW_CLOSED],
  [CaseStatus.CLOSED]: [],
  [CaseStatus.REFERRED_OUT]: [],
  [CaseStatus.NO_SHOW_CLOSED]: [],
}

const STATUS_LABEL: Record<CaseStatus, string> = {
  [CaseStatus.INTAKE]: "Intake",
  [CaseStatus.ASSESSMENT]: "Assessment",
  [CaseStatus.ACTIVE]: "Active",
  [CaseStatus.CLOSED]: "Closed",
  [CaseStatus.REFERRED_OUT]: "Referred out",
  [CaseStatus.NO_SHOW_CLOSED]: "No-show closed",
}

export function AdvanceDialog({
  open,
  onOpenChange,
  caseData,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  caseData: Case
  onConfirm: (target: CaseStatus) => Promise<void>
}) {
  const [target, setTarget] = useState<CaseStatus | "">("")
  const [submitting, setSubmitting] = useState(false)
  const options = STATUS_TRANSITIONS[caseData.status]
  const needsCounsellor = target === CaseStatus.ACTIVE && !caseData.assigned_counsellor_id

  const handleConfirm = async () => {
    if (!target || needsCounsellor) return
    setSubmitting(true)
    try {
      await onConfirm(target)
      onOpenChange(false)
      setTarget("")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Advance case status</DialogTitle>
          <DialogDescription>
            Currently {STATUS_LABEL[caseData.status]}. Choose the next status.
          </DialogDescription>
        </DialogHeader>
        <FormField label="New status" required>
          <Select value={target} onValueChange={(v) => setTarget(v as CaseStatus)}>
            <SelectTrigger>
              <SelectValue placeholder="Select…" />
            </SelectTrigger>
            <SelectContent>
              {options.map((s) => (
                <SelectItem key={s} value={s}>
                  {STATUS_LABEL[s]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
        {needsCounsellor ? (
          <p className="text-xs text-danger">
            Assign a counsellor first — Active requires one to already be set.
          </p>
        ) : null}
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleConfirm} disabled={!target || needsCounsellor || submitting}>
            {submitting ? "Advancing…" : "Advance"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function CloseCaseDialog({
  open,
  onOpenChange,
  caseData,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  caseData: Case
  onConfirm: (reason: CaseClosureReason) => Promise<void>
}) {
  const [reason, setReason] = useState<CaseClosureReason | "">("")
  const [submitting, setSubmitting] = useState(false)
  // Closing an Active case with GoalsMet requires a closure screener already
  // recorded (BE domain rule). This pass doesn't build the screener-capture
  // UI, so that combination is disabled here rather than left to fail server-side.
  const goalsMetBlocked =
    caseData.status === CaseStatus.ACTIVE && caseData.closure_screener_admin_ids.length === 0

  const handleConfirm = async () => {
    if (!reason) return
    setSubmitting(true)
    try {
      await onConfirm(reason)
      onOpenChange(false)
      setReason("")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Close case</DialogTitle>
        </DialogHeader>
        <FormField label="Closure reason" required>
          <Select value={reason} onValueChange={(v) => setReason(v as CaseClosureReason)}>
            <SelectTrigger>
              <SelectValue placeholder="Select…" />
            </SelectTrigger>
            <SelectContent>
              {Object.values(CaseClosureReason).map((r) => (
                <SelectItem
                  key={r}
                  value={r}
                  disabled={r === CaseClosureReason.GOALS_MET && goalsMetBlocked}
                >
                  {CaseClosureReasonLabel[r]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
        {reason === CaseClosureReason.GOALS_MET && goalsMetBlocked ? (
          <p className="text-xs text-danger">
            Goals-met closure needs a closure screener recorded first.
          </p>
        ) : null}
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleConfirm} disabled={!reason || submitting}>
            {submitting ? "Closing…" : "Close case"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function ReferOutDialog({
  open,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (notes: string) => Promise<void>
}) {
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const handleConfirm = async () => {
    if (!notes.trim()) return
    setSubmitting(true)
    try {
      await onConfirm(notes.trim())
      onOpenChange(false)
      setNotes("")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Refer case out</DialogTitle>
          <DialogDescription>
            Notes are required — they explain the referral and become the closure record.
          </DialogDescription>
        </DialogHeader>
        <FormField label="Notes" required>
          <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} />
        </FormField>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleConfirm} disabled={!notes.trim() || submitting}>
            {submitting ? "Referring…" : "Refer out"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** The three body shapes the BE accepts, switched on note_type. */
export function NoteBodyFields({
  noteType,
  body,
  onChange,
}: {
  noteType: ClinicalNoteType
  body: Record<string, string>
  onChange: (body: Record<string, string>) => void
}) {
  const set = (key: string) => (e: React.ChangeEvent<HTMLTextAreaElement>) =>
    onChange({ ...body, [key]: e.target.value })

  if (noteType === ClinicalNoteType.DAP) {
    return (
      <>
        <FormField label="Data" required>
          <Textarea value={body.data ?? ""} onChange={set("data")} rows={3} />
        </FormField>
        <FormField label="Assessment" required>
          <Textarea value={body.assessment ?? ""} onChange={set("assessment")} rows={3} />
        </FormField>
        <FormField label="Plan" required>
          <Textarea value={body.plan ?? ""} onChange={set("plan")} rows={3} />
        </FormField>
      </>
    )
  }
  if (noteType === ClinicalNoteType.SOAP) {
    return (
      <>
        <FormField label="Subjective" required>
          <Textarea value={body.subjective ?? ""} onChange={set("subjective")} rows={3} />
        </FormField>
        <FormField label="Objective" required>
          <Textarea value={body.objective ?? ""} onChange={set("objective")} rows={3} />
        </FormField>
        <FormField label="Assessment" required>
          <Textarea value={body.assessment ?? ""} onChange={set("assessment")} rows={3} />
        </FormField>
        <FormField label="Plan" required>
          <Textarea value={body.plan ?? ""} onChange={set("plan")} rows={3} />
        </FormField>
      </>
    )
  }
  return (
    <FormField label="Summary" required>
      <Textarea value={body.summary ?? ""} onChange={set("summary")} rows={5} />
    </FormField>
  )
}

export function noteBodyIsComplete(noteType: ClinicalNoteType, body: Record<string, string>): boolean {
  const required =
    noteType === ClinicalNoteType.DAP
      ? ["data", "assessment", "plan"]
      : noteType === ClinicalNoteType.SOAP
        ? ["subjective", "objective", "assessment", "plan"]
        : ["summary"]
  return required.every((k) => (body[k] ?? "").trim().length > 0)
}

export function CreateNoteDialog({
  open,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (noteType: ClinicalNoteType, body: Record<string, string>) => Promise<void>
}) {
  const [noteType, setNoteType] = useState<ClinicalNoteType>(ClinicalNoteType.DAP)
  const [body, setBody] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const complete = noteBodyIsComplete(noteType, body)

  const handleConfirm = async () => {
    if (!complete) return
    setSubmitting(true)
    try {
      await onConfirm(noteType, body)
      onOpenChange(false)
      setBody({})
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add clinical note</DialogTitle>
          <DialogDescription>Draft until signed. Editable only before signing.</DialogDescription>
        </DialogHeader>
        <FormField label="Note type" required>
          <Select
            value={noteType}
            onValueChange={(v) => {
              setNoteType(v as ClinicalNoteType)
              setBody({})
            }}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.values(ClinicalNoteType).map((t) => (
                <SelectItem key={t} value={t}>
                  {ClinicalNoteTypeLabel[t]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
        <NoteBodyFields noteType={noteType} body={body} onChange={setBody} />
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleConfirm} disabled={!complete || submitting}>
            {submitting ? "Saving…" : "Save note"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function bodyText(body: ClinicalNoteBody): string {
  const b = body as Record<string, string>
  if (b.summary) return b.summary
  const dap = [b.data, b.assessment, b.plan].filter(Boolean).join(" — ")
  if (dap) return dap
  const soap = [b.subjective, b.objective].filter(Boolean).join(" — ")
  return soap || "—"
}

export function NotesPanel({
  caseId: _caseId,
  notes,
  loading,
  onAddNote,
  onSign,
}: {
  caseId: string
  notes: ClinicalNote[]
  loading: boolean
  onAddNote: () => void
  onSign: (noteId: string) => void
}) {
  if (loading) return <p className="text-sm text-fg/65">Loading notes…</p>

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-fg/55">{notes.length} notes.</p>
        <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={onAddNote}>
          Add note
        </Button>
      </div>
      {notes.length === 0 ? (
        <EmptyState
          icon={HeartPulse}
          title="No notes yet"
          description="Session and contact notes for this case will appear here."
        />
      ) : (
        <div className="space-y-2">
          {notes.map((n) => (
            <DetailCard key={n.id} title={ClinicalNoteTypeLabel[n.note_type]} phiLabel="PHI · access logged">
              <p className="whitespace-pre-wrap text-sm text-fg/85">{bodyText(n.body)}</p>
              <div className="mt-3 flex items-center justify-between">
                <span className="inline-flex items-center gap-1 text-xs text-fg/55">
                  {n.signed_at ? (
                    <>
                      <Lock className="size-3" /> Signed {new Date(n.signed_at).toLocaleString()}
                    </>
                  ) : (
                    "Draft"
                  )}
                </span>
                {!n.signed_at ? (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-6 gap-1 px-2 text-xs"
                    onClick={() => onSign(n.id)}
                  >
                    <ShieldCheck className="size-3" />
                    Sign
                  </Button>
                ) : null}
              </div>
            </DetailCard>
          ))}
        </div>
      )}
    </div>
  )
}
