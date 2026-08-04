import { useState } from "react"

import { Link } from "@tanstack/react-router"
import { AlertTriangle, Phone } from "lucide-react"

import { RailSection, Stat } from "@/components/common/DetailPrimitives"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Textarea } from "@/components/ui/textarea"
import { formatDate } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { OutreachRecord } from "@/types/entities"
import { OutreachStatus } from "@/types/enums"

export function Hero({
  outreach,
  campaignName,
}: {
  outreach: OutreachRecord
  campaignName: string | null
}) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <Phone className="size-4" />
      </span>
      <h1 className="shrink truncate font-mono text-sm font-semibold leading-tight text-fg">
        {outreach.person_id}
      </h1>
      {campaignName ? (
        <Link
          to="/care-callbacks/$campaignId"
          params={{ campaignId: outreach.campaign_id }}
          className="text-xs text-fg/65 hover:text-primary"
        >
          {campaignName}
        </Link>
      ) : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <CaseStatusPill status={outreach.status} />
      {outreach.crisis_flag ? (
        <span className="inline-flex items-center gap-1 rounded-sm border border-danger/30 bg-danger-soft px-1.5 py-0.5 text-[11px] font-medium text-danger-fg">
          <AlertTriangle className="size-3" />
          Crisis
        </span>
      ) : null}
    </div>
  )
}

export function DetailRail({
  outreach,
  campaignId,
  campaignName,
  isMine,
  actionLoading,
  onAssignToMe,
  onLogAttempt,
  onOpenTerminate,
  onOpenEscalate,
}: {
  outreach: OutreachRecord
  campaignId: string
  campaignName: string | null
  isMine: boolean
  actionLoading: boolean
  onAssignToMe: () => void
  onLogAttempt: () => void
  onOpenTerminate: () => void
  onOpenEscalate: () => void
}) {
  const isTerminal =
    outreach.status === OutreachStatus.COMPLETED ||
    outreach.status === OutreachStatus.UNREACHABLE ||
    outreach.status === OutreachStatus.DECLINED ||
    outreach.status === OutreachStatus.ESCALATED
  const canLogAttempt = isMine && !isTerminal && outreach.status !== OutreachStatus.PENDING
  const canTerminate = isMine && !isTerminal && outreach.status !== OutreachStatus.PENDING

  return (
    <div className="space-y-5">
      <RailSection title="Record">
        <div className="grid grid-cols-2 gap-3">
          <Stat variant="text" label="Attempts" value={outreach.contact_attempts} />
          <Stat variant="text" label="Status" value={<CaseStatusPill status={outreach.status} />} />
          <Stat
            variant="text"
            label="Assigned"
            value={formatDate(outreach.assigned_at)}
          />
          <Stat
            variant="text"
            label="Completed"
            value={formatDate(outreach.completed_at)}
          />
        </div>
      </RailSection>

      {!isTerminal ? (
        <RailSection title="Actions">
          <div className="space-y-2">
            {outreach.status === OutreachStatus.PENDING ? (
              <Button
                size="sm"
                className="h-7 w-full gap-1.5"
                onClick={onAssignToMe}
                disabled={actionLoading}
              >
                Claim this record
              </Button>
            ) : null}
            {canLogAttempt ? (
              <Button
                size="sm"
                variant="outline"
                className="h-7 w-full gap-1.5"
                onClick={onLogAttempt}
                disabled={actionLoading}
              >
                Log contact attempt
              </Button>
            ) : null}
            {canTerminate ? (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 w-full gap-1.5"
                  onClick={onOpenTerminate}
                  disabled={actionLoading}
                >
                  Complete / no answer / decline
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 w-full gap-1.5 text-danger"
                  onClick={onOpenEscalate}
                  disabled={actionLoading}
                >
                  Escalate
                </Button>
              </>
            ) : null}
          </div>
        </RailSection>
      ) : null}

      <RailSection title="Campaign">
        <Link
          to="/care-callbacks/$campaignId"
          params={{ campaignId }}
          className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
        >
          <span
            aria-hidden
            className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <Phone className="size-3.5" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-fg">
              {campaignName ?? campaignId}
            </p>
            <p className="truncate font-mono text-[11px] text-fg/55">{campaignId}</p>
          </div>
        </Link>
      </RailSection>

      <RailSection title="Person">
        <Link
          to="/persons/$personId"
          params={{ personId: outreach.person_id }}
          className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
        >
          <span
            aria-hidden
            className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
          >
            {outreach.person_id.slice(0, 2).toUpperCase()}
          </span>
          <p className="truncate font-mono text-[11px] text-fg/55">{outreach.person_id}</p>
        </Link>
      </RailSection>
    </div>
  )
}

const TERMINATE_OPTIONS = [
  { key: "complete", label: "Completed", action: "complete" as const },
  { key: "unreachable", label: "No answer / unreachable", action: "unreachable" as const },
  { key: "declined", label: "Declined", action: "decline" as const },
]
type TerminateAction = (typeof TERMINATE_OPTIONS)[number]["action"]

export function TerminateDialog({
  open,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (action: TerminateAction, notes: string) => Promise<void>
}) {
  const [action, setAction] = useState<TerminateAction>("complete")
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const handleConfirm = async () => {
    setSubmitting(true)
    try {
      await onConfirm(action, notes.trim())
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
          <DialogTitle>Close out this record</DialogTitle>
          <DialogDescription>
            Choose how this attempt closed. Notes are optional.
          </DialogDescription>
        </DialogHeader>
        <FormField label="Outcome" required>
          <RadioGroup value={action} onValueChange={(v) => setAction(v as TerminateAction)}>
            <div className="space-y-1.5">
              {TERMINATE_OPTIONS.map((opt) => (
                <label
                  key={opt.key}
                  className={cn(
                    "flex cursor-pointer items-center gap-2 rounded-sm border px-3 py-2 text-sm",
                    action === opt.action ? "border-primary/40 bg-primary/5" : "border-fg/15",
                  )}
                >
                  <RadioGroupItem value={opt.action} />
                  {opt.label}
                </label>
              ))}
            </div>
          </RadioGroup>
        </FormField>
        <FormField label="Notes" optional htmlFor="terminate-notes">
          <Textarea id="terminate-notes" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </FormField>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleConfirm} disabled={submitting}>
            {submitting ? "Saving…" : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function EscalateDialog({
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
          <DialogTitle>Escalate</DialogTitle>
          <DialogDescription>
            Notes are required — they explain why this is being escalated.
          </DialogDescription>
        </DialogHeader>
        <FormField label="Notes" required>
          <Textarea rows={4} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </FormField>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleConfirm} disabled={!notes.trim() || submitting}>
            {submitting ? "Escalating…" : "Escalate"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function CaseStatusPill({ status }: { status: OutreachStatus }) {
  const tone =
    status === OutreachStatus.ESCALATED
      ? "border-danger/30 bg-danger-soft text-danger-fg"
      : status === OutreachStatus.COMPLETED
        ? "border-primary/30 bg-primary/10 text-primary"
        : status === OutreachStatus.CONTACTED
          ? "border-fg/25 bg-bg text-fg"
          : "border-fg/15 bg-bg text-fg/75"
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[11px] font-medium",
        tone,
      )}
    >
      {status}
    </span>
  )
}
