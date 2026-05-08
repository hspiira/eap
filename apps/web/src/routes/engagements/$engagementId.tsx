import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { useState } from "react"

import { engagementsApi } from "@/api/endpoints/engagements"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { defaultErrorMessage } from "@/lib/errors"
import { useAuthStore } from "@/store/slices/authSlice"
import { DeliverableStatus, EngagementStatus } from "@/types/enums"

export const Route = createFileRoute("/engagements/$engagementId")({
  component: EngagementDetailPage,
})

function EngagementDetailPage() {
  const { engagementId } = Route.useParams()
  const qc = useQueryClient()
  const { showSuccess, showError } = useToast()

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

  const transitionMutation = useMutation({
    mutationFn: (to: EngagementStatus) => engagementsApi.transition(engagementId, to),
    onSuccess: async (e) => {
      showSuccess(`Status: ${e.status}`)
      await qc.invalidateQueries({ queryKey: ["engagements"] })
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  if (engagementQuery.isPending) {
    return <p className="p-6 text-sm text-ink/60">Loading…</p>
  }
  if (!engagementQuery.data) {
    return <p className="p-6 text-sm text-ink/60">Engagement not found.</p>
  }
  const engagement = engagementQuery.data
  const allowed = engagementsApi.allowedTransitions(engagement.status)
  const deliverables = deliverablesQuery.data ?? []
  const timeEntries = timeQuery.data ?? []
  const timeline = timelineQuery.data ?? []

  const budgetPct = engagement.budget_hours
    ? Math.round((engagement.hours_logged / engagement.budget_hours) * 100)
    : null
  const budgetExceeded = budgetPct !== null && budgetPct > 100

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-4xl space-y-5">
        <header>
          <Link
            to="/engagements"
            className="text-xs text-ink/60 hover:text-natural hover:underline"
          >
            ← All engagements
          </Link>
          <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold text-ink">{engagement.name}</h1>
              <p className="mt-1 text-sm text-ink/70">
                {engagement.engagement_type} · started{" "}
                {new Date(engagement.start_date).toLocaleDateString()}
                {engagement.due_date
                  ? ` · due ${new Date(engagement.due_date).toLocaleDateString()}`
                  : ""}
                {" · "}
                <span className="font-medium text-ink">{engagement.status}</span>
              </p>
              {engagement.description ? (
                <p className="mt-2 text-sm text-ink/70">{engagement.description}</p>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              {allowed.map((to) => (
                <Button
                  key={to}
                  type="button"
                  variant="secondary"
                  size="sm"
                  disabled={transitionMutation.isPending}
                  onClick={() => transitionMutation.mutate(to)}
                  className="rounded-none border-ink/30 text-ink"
                >
                  → {to}
                </Button>
              ))}
            </div>
          </div>
        </header>

        <section className="grid gap-3 sm:grid-cols-4">
          <Stat label="Hours logged" value={engagement.hours_logged.toFixed(1)} />
          <Stat
            label="Budget"
            value={engagement.budget_hours ? `${engagement.budget_hours}h` : "Open-ended"}
          />
          <Stat
            label="Utilisation"
            value={budgetPct !== null ? `${budgetPct}%` : "—"}
            highlight={budgetExceeded}
          />
          <Stat
            label="Rate"
            value={
              engagement.hourly_rate
                ? `${engagement.hourly_rate} ${engagement.currency ?? ""}`
                : "—"
            }
          />
        </section>

        <DeliverablesSection
          engagementId={engagementId}
          deliverables={deliverables}
          loading={deliverablesQuery.isPending}
        />

        <TimeEntriesSection
          engagementId={engagementId}
          deliverables={deliverables}
          entries={timeEntries}
          loading={timeQuery.isPending}
        />

        <section className="border border-ink/20 bg-white p-4">
          <h2 className="text-sm font-semibold text-ink">Timeline</h2>
          {timelineQuery.isPending ? (
            <p className="mt-2 text-sm text-ink/60">Loading…</p>
          ) : timeline.length === 0 ? (
            <p className="mt-2 text-sm text-ink/60">No events yet.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {timeline.map((e) => (
                <li key={e.id} className="border-l-2 border-natural/40 pl-3">
                  <p className="text-xs text-ink/60">
                    {new Date(e.at).toLocaleString()} · {e.actor} · {e.kind}
                  </p>
                  <p className="text-ink/80">{e.message}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}

function Stat({
  label,
  value,
  highlight,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div
      className={`border p-3 ${
        highlight ? "border-amber-500/40 bg-amber-50" : "border-ink/20 bg-white"
      }`}
    >
      <div className="text-xs uppercase text-ink/60">{label}</div>
      <div className={`mt-1 text-lg font-semibold ${highlight ? "text-amber-700" : "text-ink"}`}>
        {value}
      </div>
    </div>
  )
}

interface DeliverablesSectionProps {
  engagementId: string
  deliverables: import("@/types/entities").EngagementDeliverable[]
  loading: boolean
}

function DeliverablesSection({ engagementId, deliverables, loading }: DeliverablesSectionProps) {
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

  const STATUS_OPTIONS: DeliverableStatus[] = [
    DeliverableStatus.PENDING,
    DeliverableStatus.IN_PROGRESS,
    DeliverableStatus.SUBMITTED,
    DeliverableStatus.ACCEPTED,
    DeliverableStatus.REJECTED,
  ]

  return (
    <section className="border border-ink/20 bg-white p-4 space-y-3">
      <header className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-ink">Deliverables</h2>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() => setOpen((v) => !v)}
          className="rounded-none border-ink/30 text-ink"
        >
          {open ? "Cancel" : "+ Add"}
        </Button>
      </header>

      {open && (
        <div className="space-y-2 border border-dashed border-ink/30 p-3">
          <Input
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="rounded-none"
          />
          <div className="flex gap-2">
            <Input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="rounded-none"
            />
            <Button
              type="button"
              disabled={!title.trim() || createMutation.isPending}
              onClick={() => createMutation.mutate()}
              className="rounded-none bg-natural text-white hover:bg-natural-dark"
            >
              {createMutation.isPending ? "Adding…" : "Add deliverable"}
            </Button>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-ink/60">Loading…</p>
      ) : deliverables.length === 0 ? (
        <p className="text-sm text-ink/60">No deliverables yet.</p>
      ) : (
        <ul className="divide-y divide-ink/10 border-t border-ink/10">
          {deliverables.map((d) => (
            <li key={d.id} className="flex items-center justify-between gap-3 py-2">
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink">{d.title}</p>
                <p className="text-xs text-ink/60">
                  {d.due_date ? `Due ${new Date(d.due_date).toLocaleDateString()}` : "No due date"}
                  {d.submitted_at
                    ? ` · submitted ${new Date(d.submitted_at).toLocaleDateString()}`
                    : ""}
                </p>
              </div>
              <select
                value={d.status}
                disabled={updateMutation.isPending}
                onChange={(e) =>
                  updateMutation.mutate({ id: d.id, status: e.target.value as DeliverableStatus })
                }
                className="h-8 border border-ink/30 bg-white px-2 text-xs rounded-none text-ink"
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

interface TimeEntriesSectionProps {
  engagementId: string
  deliverables: import("@/types/entities").EngagementDeliverable[]
  entries: import("@/types/entities").EngagementTimeEntry[]
  loading: boolean
}

function TimeEntriesSection({
  engagementId,
  deliverables,
  entries,
  loading,
}: TimeEntriesSectionProps) {
  const qc = useQueryClient()
  const { showError } = useToast()
  const userId = useAuthStore((s) => s.user_id) ?? "user-helen"

  const [occurredOn, setOccurredOn] = useState(new Date().toISOString().slice(0, 10))
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
    <section className="border border-ink/20 bg-white p-4 space-y-3">
      <header>
        <h2 className="text-sm font-semibold text-ink">Hours log</h2>
        <p className="text-xs text-ink/60">Hours roll up into the engagement totals.</p>
      </header>

      <div className="grid gap-2 sm:grid-cols-[8rem_5rem_1fr_10rem_auto] items-start">
        <Input
          type="date"
          value={occurredOn}
          onChange={(e) => setOccurredOn(e.target.value)}
          className="rounded-none"
        />
        <Input
          type="number"
          min={0.25}
          step={0.25}
          placeholder="Hours"
          value={hours}
          onChange={(e) => setHours(e.target.value)}
          className="rounded-none"
        />
        <Input
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="rounded-none"
        />
        <select
          value={deliverableId}
          onChange={(e) => setDeliverableId(e.target.value)}
          className="h-9 border border-ink/30 bg-white px-2 text-sm rounded-none text-ink"
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
          disabled={!canSubmit || logMutation.isPending}
          onClick={() => logMutation.mutate()}
          className="rounded-none bg-natural text-white hover:bg-natural-dark"
        >
          {logMutation.isPending ? "Logging…" : "Log"}
        </Button>
      </div>

      {loading ? (
        <p className="text-sm text-ink/60">Loading…</p>
      ) : entries.length === 0 ? (
        <p className="text-sm text-ink/60">No time logged yet.</p>
      ) : (
        <table className="w-full border border-ink/10 text-sm">
          <thead className="bg-neutral-50 text-ink">
            <tr>
              <th className="border-b border-ink/10 px-2 py-1.5 text-left font-medium">Date</th>
              <th className="border-b border-ink/10 px-2 py-1.5 text-right font-medium">Hours</th>
              <th className="border-b border-ink/10 px-2 py-1.5 text-left font-medium">By</th>
              <th className="border-b border-ink/10 px-2 py-1.5 text-left font-medium">Note</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id} className="text-ink/80">
                <td className="border-b border-ink/10 px-2 py-1.5">
                  {new Date(e.occurred_on).toLocaleDateString()}
                </td>
                <td className="border-b border-ink/10 px-2 py-1.5 text-right tabular-nums">
                  {e.hours.toFixed(2)}
                </td>
                <td className="border-b border-ink/10 px-2 py-1.5">{e.user_id}</td>
                <td className="border-b border-ink/10 px-2 py-1.5">{e.description ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
