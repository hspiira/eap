import { useState } from "react"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Briefcase,
  Clock,
  Plus,
  RotateCw,
  Users,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { engagementsApi } from "@/api/endpoints/engagements"
import { usersApi } from "@/api/endpoints/users"
import { EmptyState } from "@/components/common/EmptyState"
import { FormField } from "@/components/common/FormField"
import { PageShell } from "@/components/common/PageShell"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { EngagementDetailSkeleton } from "@/components/EngagementsPageSkeletons"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { defaultErrorMessage } from "@/lib/errors"
import { cn } from "@/lib/utils"
import {
  EngagementStatusPill,
  isOverdue,
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

export const Route = createFileRoute("/engagements/$engagementId")({
  component: EngagementDetailPage,
})

type TabValue = "overview" | "deliverables" | "hours" | "timeline"
const TAB_VALUES: ReadonlyArray<TabValue> = [
  "overview",
  "deliverables",
  "hours",
  "timeline",
]

const SELECT_CLASS =
  "flex h-9 w-full rounded-sm border border-fg/20 bg-bg px-3 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"

const DELIVERABLE_STATUS_OPTIONS: DeliverableStatus[] = [
  DeliverableStatus.PENDING,
  DeliverableStatus.IN_PROGRESS,
  DeliverableStatus.SUBMITTED,
  DeliverableStatus.ACCEPTED,
  DeliverableStatus.REJECTED,
]

function EngagementDetailPage() {
  const { engagementId } = Route.useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { showSuccess, showError } = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")

  const engagementQuery = useQuery({
    queryKey: ["engagements", "detail", engagementId],
    queryFn: () => engagementsApi.getById(engagementId),
  })
  const deliverablesQuery = useQuery({
    queryKey: ["engagements", "deliverables", engagementId],
    queryFn: () => engagementsApi.listDeliverables(engagementId),
  })
  const timeQuery = useQuery({
    queryKey: ["engagements", "time", engagementId],
    queryFn: () => engagementsApi.listTimeEntries(engagementId),
  })
  const timelineQuery = useQuery({
    queryKey: ["engagements", "timeline", engagementId],
    queryFn: () => engagementsApi.getTimeline(engagementId),
  })

  const clientId = engagementQuery.data?.client_id
  const clientQuery = useQuery({
    queryKey: ["clients", "detail", clientId ?? ""],
    queryFn: () => clientsApi.getById(clientId as string),
    enabled: !!clientId,
  })

  const leadId = engagementQuery.data?.lead_user_id
  const leadQuery = useQuery({
    queryKey: ["users", "detail", leadId ?? ""],
    queryFn: () => usersApi.getById(leadId as string),
    enabled: !!leadId,
  })

  const transitionMutation = useMutation({
    mutationFn: (to: EngagementStatus) => engagementsApi.transition(engagementId, to),
    onSuccess: async (e) => {
      showSuccess(`Status: ${e.status}`)
      await qc.invalidateQueries({ queryKey: ["engagements"] })
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  if (engagementQuery.isPending) {
    return (
      <PageShell icon={Briefcase} breadcrumb="Commercial · Engagements · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <EngagementDetailSkeleton />
        </div>
      </PageShell>
    )
  }
  if (!engagementQuery.data) {
    return (
      <PageShell icon={Briefcase} breadcrumb="Commercial · Engagements · Not found">
        <EmptyState
          icon={Briefcase}
          title="Engagement not found"
          description="It may have been cancelled or never existed."
          action={
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => navigate({ to: "/engagements" })}
            >
              <ArrowLeft className="size-4" />
              Back to engagements
            </Button>
          }
        />
      </PageShell>
    )
  }

  const engagement = engagementQuery.data
  const allowed = engagementsApi.allowedTransitions(engagement.status)
  const deliverables = deliverablesQuery.data ?? []
  const timeEntries = timeQuery.data ?? []
  const timeline = timelineQuery.data ?? []
  const client = clientQuery.data ?? null
  const lead = leadQuery.data ?? null
  const overdue = isOverdue(engagement.due_date, engagement.status)
  const budgetPct = engagement.budget_hours
    ? Math.round((engagement.hours_logged / engagement.budget_hours) * 100)
    : null
  const budgetExceeded = budgetPct !== null && budgetPct > 100

  return (
    <PageShell
      icon={Briefcase}
      breadcrumb={`Commercial · Engagements · ${engagement.name}`}
      actions={
        <>
          <button
            type="button"
            onClick={() => navigate({ to: "/engagements" })}
            aria-label="Back to engagements"
            title="Back to engagements"
            className="grid size-7 place-items-center rounded-sm text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
          >
            <ArrowLeft className="size-3.5" />
          </button>
          <button
            type="button"
            onClick={() => engagementQuery.refetch()}
            aria-label="Refresh"
            title="Refresh"
            className="grid size-7 place-items-center rounded-sm text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
          >
            <RotateCw className="size-3.5" />
          </button>
        </>
      }
    >
      <Hero engagement={engagement} client={client} overdue={overdue} />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="deliverables" count={deliverables.length}>
                  Deliverables
                </Tab>
                <Tab value="hours" count={timeEntries.length}>
                  Hours
                </Tab>
                <Tab value="timeline">Timeline</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Identity">
                    <DetailGrid>
                      <DetailRow label="Name" value={engagement.name} fullWidth />
                      <DetailRow
                        label="Description"
                        value={engagement.description}
                        fullWidth
                      />
                      <DetailRow label="Type" value={engagement.engagement_type} />
                      <DetailRow
                        label="Status"
                        value={<EngagementStatusPill status={engagement.status} />}
                      />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Schedule">
                    <DetailGrid>
                      <DetailRow
                        label="Start"
                        value={new Date(engagement.start_date).toLocaleDateString()}
                      />
                      <DetailRow
                        label="Due"
                        value={
                          engagement.due_date
                            ? new Date(engagement.due_date).toLocaleDateString()
                            : null
                        }
                      />
                      <DetailRow
                        label="Closed"
                        value={
                          engagement.closed_at
                            ? new Date(engagement.closed_at).toLocaleDateString()
                            : null
                        }
                      />
                    </DetailGrid>
                    {overdue ? (
                      <p className="mt-3 inline-flex items-center gap-1 rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[11px] font-medium text-amber-600">
                        <AlertTriangle className="size-3" />
                        Overdue — past due date and not yet delivered
                      </p>
                    ) : null}
                  </DetailCard>

                  <DetailCard title="Commercials">
                    <DetailGrid>
                      <DetailRow
                        label="Hourly rate"
                        value={
                          engagement.hourly_rate != null
                            ? `${engagement.currency ?? ""} ${engagement.hourly_rate.toLocaleString()}`.trim()
                            : null
                        }
                      />
                      <DetailRow
                        label="Budget"
                        value={
                          engagement.budget_hours
                            ? `${engagement.budget_hours}h`
                            : "Open-ended"
                        }
                      />
                      <DetailRow
                        label="Logged"
                        value={`${engagement.hours_logged.toFixed(1)}h`}
                      />
                      <DetailRow
                        label="Utilisation"
                        value={
                          budgetPct !== null ? (
                            <span
                              className={cn(
                                budgetExceeded ? "text-amber-600" : "text-fg",
                              )}
                            >
                              {budgetPct}%
                            </span>
                          ) : null
                        }
                      />
                    </DetailGrid>
                    {budgetPct !== null ? (
                      <div
                        className="mt-3 h-1 w-full overflow-hidden rounded-sm bg-fg/10"
                        aria-hidden
                      >
                        <div
                          className={cn(
                            "h-full",
                            budgetExceeded ? "bg-amber-500" : "bg-primary",
                          )}
                          style={{ width: `${Math.min(100, budgetPct)}%` }}
                        />
                      </div>
                    ) : null}
                  </DetailCard>

                  <DetailCard title="Lead">
                    {lead ? (
                      <Link
                        to="/users/$userId"
                        params={{ userId: lead.id }}
                        className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
                      >
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
                        >
                          <Users className="size-3.5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg">
                            {lead.email}
                          </p>
                        </div>
                      </Link>
                    ) : (
                      <p className="text-xs text-fg/55">No lead assigned.</p>
                    )}
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="deliverables">
                <DeliverablesPanel
                  engagementId={engagementId}
                  deliverables={deliverables}
                  loading={deliverablesQuery.isPending}
                />
              </TabPanel>

              <TabPanel value="hours">
                <HoursPanel
                  engagementId={engagementId}
                  deliverables={deliverables}
                  entries={timeEntries}
                  loading={timeQuery.isPending}
                />
              </TabPanel>

              <TabPanel value="timeline">
                <TimelinePanel timeline={timeline} loading={timelineQuery.isPending} />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              engagement={engagement}
              client={client}
              budgetPct={budgetPct}
              allowedTransitions={allowed}
              transitioning={transitionMutation.isPending}
              onTransition={(to) => transitionMutation.mutate(to)}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({
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

function DeliverablesPanel({
  engagementId,
  deliverables,
  loading,
}: {
  engagementId: string
  deliverables: EngagementDeliverable[]
  loading: boolean
}) {
  const qc = useQueryClient()
  const { showError } = useToast()
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [dueDate, setDueDate] = useState("")

  const createMutation = useMutation({
    mutationFn: () =>
      engagementsApi.createDeliverable({
        engagement_id: engagementId,
        title: title.trim(),
        due_date: dueDate || null,
      }),
    onSuccess: async () => {
      setTitle("")
      setDueDate("")
      setOpen(false)
      await qc.invalidateQueries({ queryKey: ["engagements", "deliverables", engagementId] })
      await qc.invalidateQueries({ queryKey: ["engagements", "timeline", engagementId] })
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: DeliverableStatus }) =>
      engagementsApi.updateDeliverableStatus(id, status),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["engagements", "deliverables", engagementId] })
      await qc.invalidateQueries({ queryKey: ["engagements", "timeline", engagementId] })
    },
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
                  {d.due_date
                    ? `Due ${new Date(d.due_date).toLocaleDateString()}`
                    : "No due date"}
                  {d.submitted_at
                    ? ` · submitted ${new Date(d.submitted_at).toLocaleDateString()}`
                    : ""}
                </p>
              </div>
              <select
                value={d.status}
                disabled={updateMutation.isPending}
                onChange={(e) =>
                  updateMutation.mutate({
                    id: d.id,
                    status: e.target.value as DeliverableStatus,
                  })
                }
                className={cn(SELECT_CLASS, "w-36")}
              >
                {DELIVERABLE_STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </li>
          ))}
        </ul>
      )}
    </DetailCard>
  )
}

function HoursPanel({
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
  const qc = useQueryClient()
  const { showError } = useToast()
  const userId = useAuthStore((s) => s.user_id) ?? "user-helen"

  const [occurredOn, setOccurredOn] = useState(
    new Date().toISOString().slice(0, 10),
  )
  const [hours, setHours] = useState("")
  const [description, setDescription] = useState("")
  const [deliverableId, setDeliverableId] = useState("")

  const logMutation = useMutation({
    mutationFn: () =>
      engagementsApi.logTime({
        engagement_id: engagementId,
        user_id: userId,
        occurred_on: occurredOn,
        hours: Number(hours),
        description: description.trim() || null,
        deliverable_id: deliverableId || null,
      }),
    onSuccess: async () => {
      setHours("")
      setDescription("")
      setDeliverableId("")
      await qc.invalidateQueries({ queryKey: ["engagements", "time", engagementId] })
      await qc.invalidateQueries({ queryKey: ["engagements", "detail", engagementId] })
      await qc.invalidateQueries({ queryKey: ["engagements", "timeline", engagementId] })
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
        <select
          value={deliverableId}
          onChange={(e) => setDeliverableId(e.target.value)}
          className={SELECT_CLASS}
        >
          <option value="">— Deliverable —</option>
          {deliverables.map((d) => (
            <option key={d.id} value={d.id}>
              {d.title}
            </option>
          ))}
        </select>
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
          <table className="w-full text-sm">
            <thead className="bg-bg">
              <tr className="text-left text-[11px] font-semibold uppercase tracking-wide text-fg/55">
                <th className="border-b border-fg/15 px-3 py-2">Date</th>
                <th className="w-20 border-b border-fg/15 px-3 py-2 text-right">Hours</th>
                <th className="w-40 border-b border-fg/15 px-3 py-2">By</th>
                <th className="border-b border-fg/15 px-3 py-2">Note</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-b border-fg/8 last:border-0 text-fg">
                  <td className="px-3 py-2">
                    {new Date(e.occurred_on).toLocaleDateString()}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {e.hours.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-fg/75">
                    {e.user_id}
                  </td>
                  <td className="px-3 py-2 text-fg/80">{e.description ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </DetailCard>
  )
}

function TimelinePanel({
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
                {new Date(e.at).toLocaleString()} ·{" "}
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

function TimelineKindPill({ kind }: { kind: EngagementTimelineEventKind }) {
  return (
    <span className="inline-flex items-center rounded-sm border border-fg/15 bg-bg px-1 py-0 text-[10px] font-medium text-fg/75">
      {kind}
    </span>
  )
}

function DetailRail({
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
          <Stat
            label="Hours"
            value={engagement.hours_logged.toFixed(1)}
          />
          <Stat
            label="Budget"
            value={
              engagement.budget_hours ? `${engagement.budget_hours}h` : "Open"
            }
          />
          <Stat
            label="Util"
            value={budgetPct !== null ? `${budgetPct}%` : "—"}
          />
          <Stat
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
              {clientInitial(client.name)}
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

function DetailCard({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-sm border border-fg/10 bg-surface p-4">
      <h3 className="mb-3 text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      {children}
    </section>
  )
}

function RailSection({
  title,
  children,
  className,
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={cn("space-y-2", className)}>
      <h3 className="text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      {children}
    </section>
  )
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-sm border border-fg/10 bg-surface px-3 py-2">
      <div className="text-[11px] font-medium tracking-wide text-fg/55">{label}</div>
      <div className="mt-0.5 truncate font-mono text-base font-semibold text-fg">
        {value}
      </div>
    </div>
  )
}

function DetailGrid({ children }: { children: React.ReactNode }) {
  return <dl className="grid grid-cols-2 gap-x-3 gap-y-2.5">{children}</dl>
}

function DetailRow({
  label,
  value,
  fullWidth,
}: {
  label: string
  value: React.ReactNode
  fullWidth?: boolean
}) {
  return (
    <div className={cn(fullWidth && "col-span-2")}>
      <dt className="text-[11px] font-medium tracking-wide text-fg/55">{label}</dt>
      <dd className="mt-0.5 truncate text-sm text-fg">
        {value || <span className="text-fg/40">—</span>}
      </dd>
    </div>
  )
}

function clientInitial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
}

