import { useState } from "react"

import { type QueryKey } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowRight,
  Briefcase,
  Clock,
  Plus,
} from "lucide-react"

import { engagementsApi } from "@/api/endpoints/engagements"
import {
  DetailCard,
  RailSection,
  Stat,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
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
import { formatDate, formatDateTime } from "@/lib/format"
import { useEntityMutation } from "@/lib/queries"
import {
  EngagementStatusPill,
} from "@/routes/engagements/index"
import { useAuthStore } from "@/store/slices/authSlice"
import type {
  Client,
  Engagement,
  EngagementDeliverable,
  EngagementTimeEntry,
  EngagementTimelineEvent,
} from "@/types/entities"
import type {
  EngagementTimelineEventKind} from "@/types/enums";
import {
  DeliverableStatus,
  type EngagementStatus
} from "@/types/enums"

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
          <span className="ml-1.5 font-mono text-fg/45">{client.code}</span>
        </Link>
      ) : null}
      <span className="font-mono text-xs text-fg/55">{engagement.engagement_type}</span>
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

const DELIVERABLE_STATUS_OPTIONS: DeliverableStatus[] = [
  DeliverableStatus.PENDING,
  DeliverableStatus.IN_PROGRESS,
  DeliverableStatus.SUBMITTED,
  DeliverableStatus.ACCEPTED,
  DeliverableStatus.REJECTED,
]

export function DeliverablesPanel({
  engagementId,
  deliverables,
  loading,
}: {
  engagementId: string
  deliverables: EngagementDeliverable[]
  loading: boolean
}) {
  const { showError } = useToast()
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [dueDate, setDueDate] = useState("")

  const deliverableInvalidateKeys: QueryKey[] = [
    ["engagements", "deliverables", engagementId],
    ["engagements", "timeline", engagementId],
  ]

  const createMutation = useEntityMutation({
    resource: "engagements",
    mutationFn: () =>
      engagementsApi.createDeliverable({
        engagement_id: engagementId,
        title: title.trim(),
        due_date: dueDate || null,
      }),
    skipListInvalidation: true,
    invalidateKeys: deliverableInvalidateKeys,
    onSuccess: () => {
      setTitle("")
      setDueDate("")
      setOpen(false)
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  const updateMutation = useEntityMutation({
    resource: "engagements",
    mutationFn: ({ id, status }: { id: string; status: DeliverableStatus }) =>
      engagementsApi.updateDeliverableStatus(engagementId, id, status),
    skipListInvalidation: true,
    invalidateKeys: deliverableInvalidateKeys,
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  return (
    <DetailCard title="Deliverables">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="text-xs text-fg/55">
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
            <FormField label="Due date" optional htmlFor="dl-due">
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

      {loading ? (
        <p className="text-sm text-fg/65">Loading…</p>
      ) : deliverables.length === 0 ? (
        <EmptyState
          title="No deliverables yet"
          description="Add deliverables so each artefact has its own status and can be tied to time entries."
        />
      ) : (
        <ul className="divide-y divide-fg/8">
          {deliverables.map((d) => (
            <li
              key={d.id}
              className="flex items-center justify-between gap-3 py-2.5"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-fg">{d.title}</p>
                <p className="truncate text-xs text-fg/55">
                  {d.due_date ? `Due ${formatDate(d.due_date)}` : "No due date"}
                  {d.submitted_at ? ` · submitted ${formatDate(d.submitted_at)}` : ""}
                </p>
              </div>
              <Select
                disabled={updateMutation.isPending}
                value={d.status}
                onValueChange={(v) =>
                  updateMutation.mutate({
                    id: d.id,
                    status: v as DeliverableStatus,
                  })
                }
              >
                <SelectTrigger className="w-36">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DELIVERABLE_STATUS_OPTIONS.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
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
  deliverables,
  entries,
  loading,
}: {
  engagementId: string
  deliverables: EngagementDeliverable[]
  entries: EngagementTimeEntry[]
  loading: boolean
}) {
  const { showError } = useToast()
  const userId = useAuthStore((s) => s.user_id) ?? "user-helen"

  const [occurredOn, setOccurredOn] = useState(
    new Date().toISOString().slice(0, 10),
  )
  const [hours, setHours] = useState("")
  const [description, setDescription] = useState("")
  const [deliverableId, setDeliverableId] = useState("")

  const logMutation = useEntityMutation({
    resource: "engagements",
    mutationFn: () =>
      engagementsApi.logTime({
        engagement_id: engagementId,
        user_id: userId,
        occurred_on: occurredOn,
        hours: Number(hours),
        description: description.trim() || null,
        deliverable_id: deliverableId || null,
      }),
    detailId: engagementId,
    skipListInvalidation: true,
    invalidateKeys: [
      ["engagements", "time", engagementId],
      ["engagements", "timeline", engagementId],
    ],
    onSuccess: () => {
      setHours("")
      setDescription("")
      setDeliverableId("")
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  const canSubmit = !!occurredOn && Number(hours) > 0

  return (
    <DetailCard title="Hours log">
      <p className="mb-3 text-xs text-fg/55">
        Hours roll up into the engagement totals. Tag a deliverable to keep
        utilisation per artefact.
      </p>

      <div className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-[8rem_5rem_1fr_10rem_auto]">
        <Input
          type="date"
          value={occurredOn}
          onChange={(e) => setOccurredOn(e.target.value)}
        />
        <Input
          type="number"
          inputMode="decimal"
          min={0.25}
          step={0.25}
          placeholder="Hours"
          className="font-mono"
          value={hours}
          onChange={(e) => setHours(e.target.value)}
        />
        <Input
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <Select value={deliverableId} onValueChange={setDeliverableId}>
          <SelectTrigger>
            <SelectValue placeholder="— Deliverable —" />
          </SelectTrigger>
          <SelectContent>
            {deliverables.map((d) => (
              <SelectItem key={d.id} value={d.id}>
                {d.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
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

      {loading ? (
        <p className="text-sm text-fg/65">Loading…</p>
      ) : entries.length === 0 ? (
        <EmptyState
          title="No time logged yet"
          description="Once you start logging hours, they'll roll up here and into the engagement totals."
        />
      ) : (
        <div className="overflow-hidden rounded-sm border border-fg/10">
          <Table className="w-full text-sm">
            <TableHeader className="bg-bg">
              <TableRow className="text-left hover:bg-transparent">
                <TableHead className="px-3 py-2 text-[11px] font-semibold tracking-wide">Date</TableHead>
                <TableHead className="w-20 px-3 py-2 text-right text-[11px] font-semibold tracking-wide">Hours</TableHead>
                <TableHead className="w-40 px-3 py-2 text-[11px] font-semibold tracking-wide">By</TableHead>
                <TableHead className="px-3 py-2 text-[11px] font-semibold tracking-wide">Note</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((e) => (
                <TableRow key={e.id} className="border-fg/8 last:border-0">
                  <TableCell className="px-3 py-2">
                    {formatDate(e.occurred_on)}
                  </TableCell>
                  <TableCell className="px-3 py-2 text-right font-mono">
                    {e.hours.toFixed(2)}
                  </TableCell>
                  <TableCell className="px-3 py-2 font-mono text-xs text-fg/75">
                    {e.user_id}
                  </TableCell>
                  <TableCell className="px-3 py-2 text-fg/80">{e.description ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </DetailCard>
  )
}

export function TimelinePanel({
  timeline,
  loading,
}: {
  timeline: EngagementTimelineEvent[]
  loading: boolean
}) {
  if (loading) return <p className="text-sm text-fg/65">Loading timeline…</p>
  if (timeline.length === 0) {
    return (
      <EmptyState
        title="No events yet"
        description="Lifecycle changes, deliverable updates, and hours-logged events will appear here."
      />
    )
  }
  return (
    <DetailCard title="Timeline">
      <ul className="space-y-3">
        {timeline.map((e) => (
          <li
            key={e.id}
            className="flex gap-2.5 border-l-2 border-primary/40 pl-3"
          >
            <span
              aria-hidden
              className="mt-1.5 inline-block size-1.5 -translate-x-[7.5px] rounded-full bg-primary"
            />
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-medium text-fg/55">
                {formatDateTime(e.at)} ·{" "}
                <span className="font-mono">{e.actor}</span> ·{" "}
                <TimelineKindPill kind={e.kind} />
              </p>
              <p className="mt-0.5 text-sm text-fg">{e.message}</p>
            </div>
          </li>
        ))}
      </ul>
    </DetailCard>
  )
}

export function TimelineKindPill({ kind }: { kind: EngagementTimelineEventKind }) {
  return (
    <span className="inline-flex items-center rounded-sm border border-fg/15 bg-bg px-1 py-0 text-[10px] font-medium text-fg/75">
      {kind}
    </span>
  )
}

export function DetailRail({
  engagement,
  client,
  budgetPct,
  allowedTransitions,
  transitioning,
  onTransition,
}: {
  engagement: Engagement
  client: Client | null
  budgetPct: number | null
  allowedTransitions: EngagementStatus[]
  transitioning: boolean
  onTransition: (to: EngagementStatus) => void
}) {
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat truncate
            label="Hours"
            value={engagement.hours_logged.toFixed(1)}
          />
          <Stat truncate
            label="Budget"
            value={
              engagement.budget_hours ? `${engagement.budget_hours}h` : "Open"
            }
          />
          <Stat truncate
            label="Util"
            value={budgetPct !== null ? `${budgetPct}%` : "—"}
          />
          <Stat truncate
            label="Rate"
            value={
              engagement.hourly_rate != null
                ? `${engagement.hourly_rate}${
                    engagement.currency ? ` ${engagement.currency}` : ""
                  }`
                : "—"
            }
          />
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
              className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
            >
              {nameInitials(client.name)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fg">{client.name}</p>
              <p className="truncate font-mono text-[11px] text-fg/55">{client.code}</p>
            </div>
          </Link>
        </RailSection>
      ) : null}

      <RailSection title="Lifecycle">
        {allowedTransitions.length === 0 ? (
          <p className="rounded-sm border border-fg/10 bg-surface px-3 py-2 text-xs text-fg/55">
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
