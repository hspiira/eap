function toLocalDatetime(iso: string): string {
  if (!iso) return ""
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ""
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

interface DetailRailProps {
  session: ServiceSession
  service: Service | null
  person: Person | null
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
}

import { useEffect, useState } from "react"

import { Link } from "@tanstack/react-router"
import {
  CalendarClock,
  CalendarRange,
  Lock,
  Users,
  Wrench,
} from "lucide-react"

import {
  DetailCard,
  RailSection,
  Stat,
} from "@/components/common/DetailPrimitives"
import { FormField } from "@/components/common/FormField"
import { LifecycleActions } from "@/components/common/LifecycleActions"
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
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { displayName } from "@/lib/display"
import { formatDateTime } from "@/lib/format"
import type {
  Person,
  Service,
  ServiceSession,
} from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export function Hero({
  session,
  service,
  person,
}: {
  session: ServiceSession
  service: Service | null
  person: Person | null
}) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <CalendarClock className="size-4" />
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {formatDateTime(session.scheduled_at)}
      </h1>
      {service ? (
        <Link
          to="/services/$serviceId"
          params={{ serviceId: service.id }}
          className="text-xs text-fg/65 hover:text-primary"
        >
          {service.name}
        </Link>
      ) : null}
      {person ? (
        <Link
          to="/persons/$personId"
          params={{ personId: person.id }}
          className="text-xs text-fg/65 hover:text-primary"
        >
          · {displayName(person)}
        </Link>
      ) : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={session.status} />
      <span
        title="Notes and feedback are encrypted at rest"
        className="ml-auto inline-flex shrink-0 items-center gap-1 rounded-sm border border-fg/15 bg-surface px-1.5 py-0.5 text-[10px] text-fg/55"
      >
        <Lock className="size-2.5" aria-hidden />
        Encrypted record
      </span>
    </div>
  )
}

export function DetailRail({
  session,
  service,
  person,
  onAction,
  actionLoading,
}: DetailRailProps) {
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat
            label="Duration"
            value={service?.duration_minutes != null ? `${service.duration_minutes}m` : "—"}
          />
          <Stat label="Feedback" value={session.feedback ? "Received" : "—"} />
        </div>
      </RailSection>

      <RailSection title="Linked">
        <div className="space-y-2">
          {service ? (
            <Link
              to="/services/$serviceId"
              params={{ serviceId: service.id }}
              className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
            >
              <span
                aria-hidden
                className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
              >
                <Wrench className="size-3.5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-fg">{service.name}</p>
                <p className="truncate text-[11px] text-fg/55">
                  {service.service_type ?? "—"}
                </p>
              </div>
            </Link>
          ) : null}
          {person ? (
            <Link
              to="/persons/$personId"
              params={{ personId: person.id }}
              className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
            >
              <span
                aria-hidden
                className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
              >
                <Users className="size-3.5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-fg">
                  {displayName(person)}
                </p>
                <p className="truncate text-[11px] text-fg/55">{person.person_type}</p>
              </div>
            </Link>
          ) : null}
        </div>
      </RailSection>

      <RailSection title="Lifecycle">
        <LifecycleActions
          entityId={session.id}
          currentStatus={session.status}
          kind="session"
          onAction={onAction}
          loading={actionLoading}
        />
      </RailSection>
    </div>
  )
}

export function FeedbackPanel({
  session,
  onSubmit,
}: {
  session: ServiceSession
  onSubmit: (feedback: string) => Promise<void>
}) {
  const [feedback, setFeedback] = useState(session.feedback ?? "")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setFeedback(session.feedback ?? "")
  }, [session])

  const submit = async () => {
    setSaving(true)
    try {
      await onSubmit(feedback)
    } finally {
      setSaving(false)
    }
  }

  return (
    <DetailCard title="Subject feedback" phiLabel="PHI · access logged">
      <div className="space-y-4">
        <FormField label="Feedback" optional htmlFor="ss-feedback">
          <Textarea
            id="ss-feedback"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Anything the subject shared about the session…"
            rows={4}
          />
        </FormField>
        <div className="flex justify-end">
          <Button size="sm" onClick={submit} disabled={saving || !feedback.trim()}>
            {saving ? "Saving…" : "Save feedback"}
          </Button>
        </div>
      </div>
    </DetailCard>
  )
}

export function CompleteDialog({
  open,
  onOpenChange,
  defaultDuration,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  defaultDuration: number
  onConfirm: (duration: number, notes: string) => Promise<void>
}) {
  const [duration, setDuration] = useState(String(defaultDuration))
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (open) {
      setDuration(String(defaultDuration))
      setNotes("")
    }
  }, [open, defaultDuration])

  const minutes = Number(duration)
  const valid = Number.isFinite(minutes) && minutes > 0 && notes.trim().length > 0

  const handleConfirm = async () => {
    if (!valid) return
    setSubmitting(true)
    try {
      await onConfirm(minutes, notes.trim())
      onOpenChange(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Complete session</DialogTitle>
          <DialogDescription>
            Duration and a session note become part of the clinical record.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <FormField label="Duration (minutes)" required htmlFor="complete-duration">
            <Input
              id="complete-duration"
              type="number"
              min={1}
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
          </FormField>
          <FormField label="Session notes" required htmlFor="complete-notes">
            <Textarea
              id="complete-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="What happened in this session?"
              rows={3}
            />
          </FormField>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Back
          </Button>
          <Button size="sm" onClick={handleConfirm} disabled={!valid || submitting}>
            {submitting ? "Saving…" : "Complete session"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function CancelDialog({
  open,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (reason: string) => Promise<void>
}) {
  const [reason, setReason] = useState("")
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (open) setReason("")
  }, [open])

  const handleConfirm = async () => {
    if (!reason.trim()) return
    setSubmitting(true)
    try {
      await onConfirm(reason.trim())
      onOpenChange(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Cancel session</DialogTitle>
          <DialogDescription>
            The reason is recorded on the session.
          </DialogDescription>
        </DialogHeader>
        <FormField label="Reason" required htmlFor="cancel-reason">
          <Textarea
            id="cancel-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Why is this session being cancelled?"
            rows={3}
          />
        </FormField>
        <DialogFooter>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Back
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={handleConfirm}
            disabled={!reason.trim() || submitting}
          >
            {submitting ? "Saving…" : "Cancel session"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function RescheduleDialog({
  open,
  onOpenChange,
  currentISO,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentISO: string
  onConfirm: (iso: string, notes: string) => Promise<void>
}) {
  const [scheduled, setScheduled] = useState(toLocalDatetime(currentISO))
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (open) {
      setScheduled(toLocalDatetime(currentISO))
      setNotes("")
    }
  }, [open, currentISO])

  const handleConfirm = async () => {
    if (!scheduled) return
    setSubmitting(true)
    try {
      await onConfirm(new Date(scheduled).toISOString(), notes)
      onOpenChange(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Reschedule session</DialogTitle>
          <DialogDescription>
            <CalendarRange className="mr-1 inline size-3" />
            Previous time: {formatDateTime(currentISO)}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <FormField label="New scheduled time" required htmlFor="reschedule-when">
            <Input
              id="reschedule-when"
              type="datetime-local"
              value={scheduled}
              onChange={(e) => setScheduled(e.target.value)}
            />
          </FormField>
          <FormField label="Reason / notes" optional htmlFor="reschedule-notes">
            <Input
              id="reschedule-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Why is this being rescheduled?"
            />
          </FormField>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={handleConfirm}
            disabled={!scheduled || submitting}
          >
            {submitting ? "Saving…" : "Reschedule"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
