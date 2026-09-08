import { useState } from "react"

import { type QueryKey } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { AlertTriangle, ArrowRight, Briefcase, Clock, Plus } from "lucide-react"

import { engagementsApi } from "@/api/endpoints/engagements"
import { DetailCard, RailSection, Stat } from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { nameInitials } from "@/lib/display"
import { defaultErrorMessage } from "@/lib/errors"
import { formatDate, formatDay } from "@/lib/format"
import { useEntityMutation } from "@/lib/queries"
import { EngagementStatusPill } from "@/routes/engagements/index"
import { useAuthStore } from "@/store/slices/authSlice"
import type {
  Client,
  DeliverableStatusValue,
  Engagement,
  EngagementDeliverable,
  EngagementStatusValue,
  EngagementSummary,
  EngagementTimeEntry,
} from "@/types/entities"
import { engagementHours } from "@/types/entities"
import { DeliverableStatus } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

export function Hero({
  engagement,
  client,
  overdue,
}: {
  engagement: Engagement
  client: Client | null
  overdue: boolean
}) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <Briefcase className="size-4" />
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {engagement.name}
      </h1>
      {client ? (
        <Link
          to="/clients/$clientId"
          params={{ clientId: client.id }}
          className="text-xs text-fg/65 hover:text-primary"
        >
          {client.name}
          <span className="ml-1.5 text-fg-subtle">{client.code}</span>
        </Link>
      ) : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <EngagementStatusPill status={engagement.status} />
      {overdue ? (
        <span className="inline-flex items-center gap-1 rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[11px] font-medium text-amber-600">
          <AlertTriangle className="size-3" />
          Overdue
        </span>
      ) : null}
    </div>
  )
}

/** Query key for an engagement's summary, which every child mutation changes. */
function summaryKey(engagementId: string): QueryKey[] {
  return [["engagements", "summary", engagementId]]
}

const DELIVERABLE_STATUS_OPTIONS: DeliverableStatusValue[] = [
  DeliverableStatus.PENDING,
  DeliverableStatus.IN_PROGRESS,
  DeliverableStatus.DELIVERED,
  DeliverableStatus.ACCEPTED,
]

export function DeliverablesPanel({
  engagementId,
  deliverables,
}: {
  engagementId: string
  deliverables: EngagementDeliverable[]
}) {
  const { showError } = useToast()
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [dueDate, setDueDate] = useState("")

  const createMutation = useEntityMutation({
    resource: "engagements",
    mutationFn: () =>
      engagementsApi.createDeliverable(engagementId, {
        title: title.trim(),
        due_date: dueDate || null,
      }),
    detailId: engagementId,
    skipListInvalidation: true,
    invalidateKeys: summaryKey(engagementId),
    onSuccess: () => {
      setTitle("")
      setDueDate("")
      setOpen(false)
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  const updateMutation = useEntityMutation({
    resource: "engagements",
    mutationFn: ({ id, status }: { id: string; status: DeliverableStatusValue }) =>
      engagementsApi.updateDeliverableStatus(engagementId, id, status),
    detailId: engagementId,
    skipListInvalidation: true,
    invalidateKeys: summaryKey(engagementId),
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  return (
    <DetailCard title="Deliverables">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="text-xs text-fg-muted">
          {deliverables.length} deliverable{deliverables.length === 1 ? "" : "s"}
        </p>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="h-7 gap-1.5 px-2.5"
          onClick={() => setOpen((v) => !v)}
        >
          <Plus className="size-3.5" />
          {open ? "Cancel" : "Add"}
        </Button>
      </div>

      {open ? (
        <div className="mb-3 space-y-2 rounded-sm border border-dashed border-fg/15 bg-bg p-3">
          <FormField label="Title" required htmlFor="dl-title">
            <Input
              id="dl-title"
              placeholder="e.g. First-pass policy draft"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </FormField>
          <div className="grid grid-cols-[1fr_auto] gap-2">
            <FormField label="Due date" htmlFor="dl-due">
              <Input
                id="dl-due"
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </FormField>
            <div className="self-end">
              <Button
                type="button"
                size="sm"
                disabled={!title.trim() || createMutation.isPending}
                onClick={() => createMutation.mutate()}
              >
                {createMutation.isPending ? "Adding…" : "Add deliverable"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {deliverables.length === 0 ? (
        <EmptyState
          title="No deliverables yet"
          description="Add deliverables so each artefact has its own status and can be tied to time entries."
        />
      ) : (
        <ul className="divide-y divide-fg/8">
          {deliverables.map((d) => (
            <li key={d.id} className="flex items-center justify-between gap-3 py-2.5">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-fg">{d.title}</p>
                <p className="truncate text-xs text-fg-muted">
                  {d.due_date ? `Due ${formatDate(d.due_date)}` : "No due date"}
                  {d.delivered_at ? ` · delivered ${formatDate(d.delivered_at)}` : ""}
                </p>
              </div>
              <Select
                disabled={updateMutation.isPending}
                value={d.status}
                onValueChange={(v) =>
                  updateMutation.mutate({
                    id: d.id,
                    status: v as DeliverableStatusValue,
                  })
                }
              >
                <SelectTrigger className="w-36">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DELIVERABLE_STATUS_OPTIONS.map((s) => (
                    <SelectItem key={s} value={s}>
                      {getStatusLabel(s)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </li>
          ))}
        </ul>
      )}
    </DetailCard>
  )
}

export function HoursPanel({
  engagementId,
  entries,
}: {
  engagementId: string
  entries: EngagementTimeEntry[]
}) {
  const { showError } = useToast()
  const userId = useAuthStore((s) => s.user_id) ?? "user-helen"

  const [loggedOn, setLoggedOn] = useState(new Date().toISOString().slice(0, 10))
  const [hours, setHours] = useState("")
  const [note, setNote] = useState("")

  const logMutation = useEntityMutation({
    resource: "engagements",
    mutationFn: () =>
      engagementsApi.logTime(engagementId, {
        user_id: userId,
        logged_on: loggedOn,
        hours: Number(hours),
        note: note.trim() || null,
      }),
    detailId: engagementId,
    skipListInvalidation: true,
    invalidateKeys: summaryKey(engagementId),
    onSuccess: () => {
      setHours("")
      setNote("")
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  const canSubmit = !!loggedOn && Number(hours) > 0

  return (
    <DetailCard title="Hours log">
      <p className="mb-3 text-xs text-fg-muted">
        Hours roll up into the engagement totals. Tag a deliverable to keep utilisation per
        artefact.
      </p>

      <div className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-[8rem_5rem_1fr_10rem_auto]">
        <Input type="date" value={loggedOn} onChange={(e) => setLoggedOn(e.target.value)} />
        <Input
          type="number"
          inputMode="decimal"
          min={0.25}
          step={0.25}
          placeholder="Hours"
          className="tabular-nums"
          value={hours}
          onChange={(e) => setHours(e.target.value)}
        />
        <Input placeholder="Note" value={note} onChange={(e) => setNote(e.target.value)} />
        <Button
          type="button"
          size="sm"
          className="h-9 gap-1.5"
          disabled={!canSubmit || logMutation.isPending}
          onClick={() => logMutation.mutate()}
        >
          <Clock className="size-3.5" />
          {logMutation.isPending ? "Logging…" : "Log"}
        </Button>
      </div>

      {entries.length === 0 ? (
        <EmptyState
          title="No time logged yet"
          description="Once you start logging hours, they'll roll up here and into the engagement totals."
        />
      ) : (
        <div className="overflow-hidden rounded-sm border border-fg/10">
          <Table className="w-full text-sm">
            <TableHeader className="bg-bg">
              <TableRow className="text-left hover:bg-transparent">
                <TableHead className="px-3 py-2 text-[11px] font-semibold tracking-wide">
                  Date
                </TableHead>
                <TableHead className="w-20 px-3 py-2 text-right text-[11px] font-semibold tracking-wide">
                  Hours
                </TableHead>
                <TableHead className="w-40 px-3 py-2 text-[11px] font-semibold tracking-wide">
                  By
                </TableHead>
                <TableHead className="px-3 py-2 text-[11px] font-semibold tracking-wide">
                  Note
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((e) => (
                <TableRow key={e.id} className="border-fg/8 last:border-0">
                  <TableCell className="px-3 py-2">{formatDay(e.logged_on)}</TableCell>
                  <TableCell className="px-3 py-2 text-right tabular-nums">
                    {e.hours.toFixed(2)}
                  </TableCell>
                  <TableCell className="px-3 py-2 text-xs text-fg/75 font-mono">
                    {e.user_id}
                  </TableCell>
                  <TableCell className="px-3 py-2 text-fg/80">{e.note ?? "-"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </DetailCard>
  )
}

/**
 * `GET /engagements/{id}/summary` returns totals, a deliverable mix and hours
 * by user. It is not a chronological feed, and it used to be rendered as one:
 * the adapter cast the summary object to an event array and mapped over it
 * (MODULES_REPAIR_PLAN ENG-01).
 */
export function SummaryPanel({
  summary,
  loading,
  error,
  onRetry,
}: {
  summary: EngagementSummary | null
  loading: boolean
  error: string | null
  onRetry: () => void
}) {
  if (loading) return <p className="text-sm text-fg/65">Computing summary…</p>
  if (error) return <ErrorState message={error} onRetry={onRetry} />
  if (!summary) {
    return (
      <EmptyState
        title="Summary unavailable"
        description="The engagement summary could not be loaded."
      />
    )
  }

  const mix = Object.entries(summary.deliverable_mix)
  const byUser = Object.entries(summary.hours_by_user)
  return (
    <div className="space-y-4">
      <DetailCard title="Totals">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat truncate label="Deliverables" value={String(summary.deliverable_count)} />
          <Stat truncate label="Hours" value={summary.total_hours.toFixed(1)} />
          <Stat truncate label="Start" value={formatDate(summary.period_start)} />
          <Stat truncate label="End" value={formatDate(summary.period_end)} />
        </div>
      </DetailCard>

      <DetailCard title="Deliverable mix">
        {mix.length === 0 ? (
          <p className="text-xs text-fg-muted">No deliverables yet.</p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {mix.map(([status, count]) => (
              <li key={status} className="flex items-center justify-between gap-3 py-2 text-sm">
                <span className="text-fg/80">{getStatusLabel(status)}</span>
                <span className="tabular-nums text-fg">{count}</span>
              </li>
            ))}
          </ul>
        )}
      </DetailCard>

      <DetailCard title="Hours by user">
        {byUser.length === 0 ? (
          <p className="text-xs text-fg-muted">No time logged yet.</p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {byUser.map(([userId, hours]) => (
              <li key={userId} className="flex items-center justify-between gap-3 py-2 text-sm">
                <span className="truncate font-mono text-xs text-fg/75">{userId}</span>
                <span className="tabular-nums text-fg">{hours.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        )}
      </DetailCard>
    </div>
  )
}

export function DetailRail({
  engagement,
  client,
  allowedTransitions,
  transitioning,
  onTransition,
}: {
  engagement: Engagement
  client: Client | null
  allowedTransitions: EngagementStatusValue[]
  transitioning: boolean
  onTransition: (to: EngagementStatusValue) => void
}) {
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat truncate label="Hours" value={engagementHours(engagement).toFixed(1)} />
          <Stat truncate label="Deliverables" value={String(engagement.deliverables.length)} />
          <Stat truncate label="Start" value={formatDate(engagement.period_start)} />
          <Stat truncate label="End" value={formatDate(engagement.period_end)} />
        </div>
      </RailSection>

      {client ? (
        <RailSection title="Client">
          <Link
            to="/clients/$clientId"
            params={{ clientId: client.id }}
            className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
          >
            <span
              aria-hidden
              className="grid size-7 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
            >
              {nameInitials(client.name)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fg">{client.name}</p>
              <p className="truncate text-[11px] text-fg-muted">{client.code}</p>
            </div>
          </Link>
        </RailSection>
      ) : null}

      <RailSection title="Lifecycle">
        {allowedTransitions.length === 0 ? (
          <p className="rounded-sm border border-fg/10 bg-surface px-3 py-2 text-xs text-fg-muted">
            No transitions available from <strong>{engagement.status}</strong>.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {allowedTransitions.map((to) => (
              <Button
                key={to}
                type="button"
                variant="outline"
                size="sm"
                disabled={transitioning}
                onClick={() => onTransition(to)}
                className="gap-1.5"
              >
                <ArrowRight className="size-3" />
                {to}
              </Button>
            ))}
          </div>
        )}
      </RailSection>
    </div>
  )
}
