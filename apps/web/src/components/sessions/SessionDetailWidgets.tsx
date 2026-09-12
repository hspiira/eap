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
  member: Member | null
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
}

import { useEffect, useMemo, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { CalendarClock, CalendarRange, Lock, MessageSquare, Users } from "lucide-react"

import { casesApi } from "@/api/endpoints/cases"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  LinkRow,
  RailSection,
} from "@/components/common/DetailPrimitives"
import { FormField } from "@/components/common/FormField"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import {
  EligibilityFailureNotice,
  eligibilityReasons,
} from "@/components/sessions/EligibilityFailureNotice"
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
import { Textarea } from "@/components/ui/textarea"
import { useHasClinicalScope } from "@/hooks/useCanWrite"
import { memberLabel } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDateTime } from "@/lib/format"
import type { ErrorDetail } from "@/types/api"
import type { Member, Service, ServiceSession } from "@/types/entities"
import { CaseStatus, SessionAttendance } from "@/types/enums"
import type { LifecycleAction } from "@/utils/lifecycleConfig"
import { getStatusLabel } from "@/utils/statusColors"

/**
 * The session's identity, which is not the same for both kinds of session.
 *
 * A company-wide session has no member to name, so it is identified by what was
 * delivered and to which client. Naming it by date alone, and hunting for a
 * member that does not exist, is what the page used to do.
 */
export function Hero({
  session,
  service,
  member,
}: {
  session: ServiceSession
  service: Service | null
  member: Member | null
}) {
  const companyWide = session.attendance === SessionAttendance.COMPANY_WIDE
  const serviceName = service?.name ?? session.service_name
  const subject = companyWide
    ? session.client_name
    : member
      ? memberLabel(member)
      : session.member_display_label
  const title = companyWide && serviceName && subject ? `${serviceName} at ${subject}` : serviceName

  return (
    <div className="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b border-fg/10 bg-gradient-to-r from-primary/[0.06] via-surface to-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        {companyWide ? <Users className="size-4" /> : <CalendarClock className="size-4" />}
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {title ?? formatDateTime(session.scheduled_at)}
      </h1>
      {title ? (
        <span className="text-xs text-fg/65">{formatDateTime(session.scheduled_at)}</span>
      ) : null}
      {!companyWide && subject ? (
        session.member_id ? (
          <Link
            to="/members/$memberId"
            params={{ memberId: session.member_id }}
            className="text-xs text-fg/65 hover:text-primary"
          >
            · {subject}
          </Link>
        ) : (
          <span className="text-xs text-fg/65">· {subject}</span>
        )
      ) : null}
      {session.session_type ? (
        <span className="shrink-0 rounded-sm border border-fg/15 px-1.5 py-0.5 text-[10px] text-fg-muted">
          {getStatusLabel(session.session_type)}
        </span>
      ) : null}
      {session.category ? (
        <span className="shrink-0 rounded-sm border border-fg/15 px-1.5 py-0.5 text-[10px] text-fg-muted">
          {getStatusLabel(session.category)}
        </span>
      ) : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={session.status} />
      <span
        title="Notes, feedback, issue topic and partner name are encrypted at rest"
        className="ml-auto inline-flex shrink-0 items-center gap-1 rounded-sm border border-fg/15 bg-surface px-1.5 py-0.5 text-[10px] text-fg-muted"
      >
        <Lock className="size-2.5" aria-hidden />
        Encrypted at rest
      </span>
    </div>
  )
}

/**
 * What this session records about itself.
 *
 * Duration is the session's own recorded minutes. The rail used to show the
 * service's nominal duration, which is what a session of this kind is meant to
 * take, not what this one took.
 */
export function DetailRail({ session, service, member, onAction, actionLoading }: DetailRailProps) {
  const companyWide = session.attendance === SessionAttendance.COMPANY_WIDE
  const glance = (value: string | null) =>
    value ? <span className="font-semibold tabular-nums">{value}</span> : null
  return (
    <div className="border border-fg/10 bg-surface p-4">
      <RailSection title="At a glance">
        <DetailGrid>
          <DetailRow
            label="Duration"
            value={glance(session.duration != null ? `${session.duration}m` : null)}
          />
          <DetailRow
            label={companyWide ? "Attended" : "Session no."}
            value={glance(
              companyWide
                ? session.headcount != null
                  ? String(session.headcount)
                  : null
                : session.session_number != null
                  ? `#${session.session_number}`
                  : null,
            )}
          />
          <DetailRow
            label="Rate"
            value={glance(
              session.rate_ugx != null ? `UGX ${session.rate_ugx.toLocaleString()}` : null,
            )}
          />
          <DetailRow
            label="Reschedules"
            value={glance(
              session.reschedule_count != null ? String(session.reschedule_count) : "0",
            )}
          />
        </DetailGrid>
      </RailSection>

      <RailSection title="Linked" className="mt-4 border-t border-fg/10 pt-4">
        <DetailGrid>
          {service ? (
            <LinkRow
              label="Service"
              value={service.name}
              to="/services/$serviceId"
              params={{ serviceId: service.id }}
            />
          ) : null}
          <LinkRow
            label="Client"
            value={session.client_name ?? "Open client"}
            to="/clients/$clientId"
            params={{ clientId: session.client_id }}
          />
          {member ? (
            <LinkRow
              label="Member"
              value={memberLabel(member)}
              to="/members/$memberId"
              params={{ memberId: member.id }}
            />
          ) : null}
        </DetailGrid>
      </RailSection>

      <RailSection title="Lifecycle" className="mt-4 border-t border-fg/10 pt-4">
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
    <DetailCard title="Feedback" icon={MessageSquare} phiLabel="PHI · access logged">
      <div className="space-y-4">
        <FormField label="Feedback" htmlFor="ss-feedback">
          <Textarea
            id="ss-feedback"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="What the member shared"
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

const NO_CASE = "__none__"

/** A closed case cannot absorb a drawdown, so it is not worth offering. */
const CLOSED_CASE_STATUSES: ReadonlyArray<CaseStatus> = [
  CaseStatus.CLOSED,
  CaseStatus.REFERRED_OUT,
  CaseStatus.NO_SHOW_CLOSED,
]

export function CompleteDialog({
  open,
  onOpenChange,
  defaultDuration,
  clientId,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  defaultDuration: number
  /**
   * The session's client. Cases carry no member id, so this is the only link
   * available. Undefined while the member is still loading, which suppresses
   * the picker rather than offering every client's cases.
   */
  clientId?: string | null
  onConfirm: (duration: number, notes: string, caseId?: string) => Promise<void>
}) {
  const [duration, setDuration] = useState(String(defaultDuration))
  const [notes, setNotes] = useState("")
  const [caseId, setCaseId] = useState(NO_CASE)
  const [submitting, setSubmitting] = useState(false)

  // Naming a case is what draws the session down against its authorization.
  // Only a clinical-scoped user may list cases, and the API fails closed, so
  // the picker is not rendered at all without the scope.
  const { hasScope } = useHasClinicalScope()
  const casesQuery = useQuery({
    queryKey: ["cases", "list"],
    queryFn: casesApi.list,
    enabled: open && hasScope,
    staleTime: 60_000,
  })
  const cases = useMemo(() => {
    // Fail closed without a client. Drawing a session down against another
    // client's authorization is worse than not drawing it down at all, and
    // the caller cannot always tell the two lists apart.
    if (!clientId) return []
    const rows = casesQuery.data ?? []
    return rows.filter((c) => c.client_id === clientId && !CLOSED_CASE_STATUSES.includes(c.status))
  }, [casesQuery.data, clientId])

  useEffect(() => {
    if (open) {
      setDuration(String(defaultDuration))
      setNotes("")
      setCaseId(NO_CASE)
    }
  }, [open, defaultDuration])

  const minutes = Number(duration)
  const valid = Number.isFinite(minutes) && minutes > 0 && notes.trim().length > 0

  const handleConfirm = async () => {
    if (!valid) return
    setSubmitting(true)
    try {
      await onConfirm(minutes, notes.trim(), caseId === NO_CASE ? undefined : caseId)
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
              placeholder="What happened"
              rows={3}
            />
          </FormField>
          {hasScope ? (
            <FormField
              label="Draw down against case"
              htmlFor="complete-case"
              hint="Choosing a case spends one authorized session from it."
            >
              <Select value={caseId} onValueChange={setCaseId}>
                <SelectTrigger id="complete-case" className="rounded-none">
                  <SelectValue placeholder={casesQuery.isPending ? "Loading cases…" : "No case"} />
                </SelectTrigger>
                <SelectContent className="rounded-none">
                  <SelectItem value={NO_CASE} className="rounded-none">
                    No case
                  </SelectItem>
                  {cases.map((row) => (
                    <SelectItem key={row.id} value={row.id} className="rounded-none">
                      {row.clinical_subject_id} · {row.presenting_problem}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>
          ) : null}
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
          <DialogDescription>The reason is recorded on the session.</DialogDescription>
        </DialogHeader>
        <FormField label="Reason" required htmlFor="cancel-reason">
          <Textarea
            id="cancel-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Why it was cancelled"
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
  const [refused, setRefused] = useState<ErrorDetail[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setScheduled(toLocalDatetime(currentISO))
      setNotes("")
      setRefused(null)
      setError(null)
    }
  }, [open, currentISO])

  // Rescheduling reapplies the booking gate, so a new time can be refused for
  // the practitioner or for the affiliation that no longer covers it. The
  // dialog stays open and shows why, rather than closing as if it had worked.
  const handleConfirm = async () => {
    if (!scheduled) return
    setSubmitting(true)
    setRefused(null)
    setError(null)
    try {
      await onConfirm(new Date(scheduled).toISOString(), notes)
      onOpenChange(false)
    } catch (err) {
      const reasons = eligibilityReasons(err)
      if (reasons) setRefused(reasons)
      else setError(normalizeErrorMessage(err, "Could not reschedule this session"))
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
          {refused ? <EligibilityFailureNotice reasons={refused} /> : null}
          {error ? (
            <p
              role="alert"
              className="border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-fg"
            >
              {error}
            </p>
          ) : null}
          <FormField label="New scheduled time" required htmlFor="reschedule-when">
            <Input
              id="reschedule-when"
              type="datetime-local"
              value={scheduled}
              onChange={(e) => setScheduled(e.target.value)}
            />
          </FormField>
          <FormField label="Reason" htmlFor="reschedule-notes">
            <Input
              id="reschedule-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Why it moved"
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
          <Button size="sm" onClick={handleConfirm} disabled={!scheduled || submitting}>
            {submitting ? "Saving…" : "Reschedule"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
