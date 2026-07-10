import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, Printer } from "lucide-react"

import { incidentsApi } from "@/api/endpoints/incidents"
import { SeverityBadge } from "@/components/common/SeverityBadge"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useEntityMutation } from "@/lib/queries"
import type { IncidentTimelineEvent } from "@/types/entities"

export const Route = createFileRoute("/incidents/$incidentId")({
  component: IncidentDetailPage,
})

function IncidentDetailPage() {
  const { incidentId } = Route.useParams()

  const incidentQuery = useQuery({
    queryKey: ["incidents", "detail", incidentId],
    queryFn: () => incidentsApi.getById(incidentId),
  })
  const timelineQuery = useQuery({
    queryKey: ["incidents", "timeline", incidentId],
    queryFn: () => incidentsApi.getTimeline(incidentId),
  })

  const [note, setNote] = useState("")
  const noteMutation = useEntityMutation({
    resource: "incidents",
    mutationFn: (message: string) => incidentsApi.appendNote(incidentId, message),
    detailId: incidentId,
    skipListInvalidation: true,
    invalidateKeys: [["incidents", "timeline", incidentId]],
    onSuccess: () => setNote(""),
  })

  const handlePrint = () => {
    if (typeof window !== "undefined") window.print()
  }

  const handleNoteSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (note.trim().length === 0) return
    noteMutation.mutate(note.trim())
  }

  if (incidentQuery.isPending) {
    return (
      <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
        <p className="text-fg/70">Loading incident…</p>
      </div>
    )
  }
  if (incidentQuery.isError || !incidentQuery.data) {
    return (
      <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
        <p className="text-fg/70">Couldn&apos;t load this incident.</p>
        <Link to="/incidents" className="text-sm text-primary hover:underline">
          ← Back to incidents
        </Link>
      </div>
    )
  }

  const inc = incidentQuery.data
  const timeline = timelineQuery.data ?? []

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6 print:p-0">
      <div className="mx-auto max-w-3xl space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-4 print:hidden">
          <div className="min-w-0">
            <Link
              to="/incidents"
              className="inline-flex h-8 items-center gap-1.5 text-sm text-fg/70 hover:text-fg"
            >
              <ArrowLeft className="h-4 w-4" />
              Incidents
            </Link>
            <h1 className="mt-1 text-xl font-semibold text-fg">{inc.title}</h1>
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="rounded-none border-fg/30 text-fg"
            onClick={handlePrint}
          >
            <Printer className="mr-2 h-4 w-4" />
            Print after-action
          </Button>
        </header>

        <article className="space-y-6 border border-fg/20 bg-white p-6 print:border-0 print:p-0">
          <section>
            <p className="text-xs tracking-wide text-fg/60">Critical incident</p>
            <h2 className="mt-1 text-2xl font-semibold text-fg">{inc.title}</h2>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <SeverityBadge severity={inc.severity} />
              <StatusBadge status={inc.status} />
              <span className="text-xs text-fg/60">
                Occurred {new Date(inc.occurred_at).toLocaleString()}
              </span>
            </div>
            <dl className="mt-4 grid gap-4 sm:grid-cols-3">
              <div>
                <dt className="text-xs text-fg/60">Affected population</dt>
                <dd className="text-sm text-fg">{inc.affected_population}</dd>
              </div>
              <div>
                <dt className="text-xs text-fg/60">Linked sessions</dt>
                <dd className="text-sm text-fg">{inc.linked_session_ids?.length ?? 0}</dd>
              </div>
              <div>
                <dt className="text-xs text-fg/60">Client</dt>
                <dd className="text-sm text-fg font-mono break-all">{inc.client_id}</dd>
              </div>
            </dl>
          </section>

          <section>
            <h3 className="text-sm font-semibold text-fg">Description</h3>
            <p className="mt-2 whitespace-pre-wrap text-sm text-fg/90">{inc.description}</p>
          </section>

          <section>
            <h3 className="text-sm font-semibold text-fg">Timeline</h3>
            {timelineQuery.isPending ? (
              <p className="mt-2 text-sm text-fg/60">Loading timeline…</p>
            ) : (
              <ol className="mt-3 space-y-3 border-l border-fg/20 pl-4">
                {timeline.map((event) => (
                  <TimelineRow key={event.id} event={event} />
                ))}
              </ol>
            )}
          </section>

          {inc.resolution_notes && (
            <section>
              <h3 className="text-sm font-semibold text-fg">Resolution notes</h3>
              <p className="mt-2 whitespace-pre-wrap text-sm text-fg/90">{inc.resolution_notes}</p>
            </section>
          )}
        </article>

        <section className="border border-fg/20 bg-white p-4 print:hidden">
          <h3 className="text-sm font-semibold text-fg">Add note</h3>
          <form onSubmit={handleNoteSubmit} className="mt-2 flex flex-col gap-2 sm:flex-row">
            <Input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Add a timeline note…"
              className="rounded-none border-fg/30"
            />
            <Button
              type="submit"
              disabled={noteMutation.isPending || note.trim().length === 0}
              className="rounded-none bg-primary text-white hover:bg-primary"
            >
              {noteMutation.isPending ? "Saving…" : "Add note"}
            </Button>
          </form>
        </section>
      </div>
    </div>
  )
}

function TimelineRow({ event }: { event: IncidentTimelineEvent }) {
  return (
    <li className="relative">
      <span
        className="absolute -left-4.75 top-1.5 inline-block h-3 w-3 rounded-full bg-primary"
        aria-hidden
      />
      <p className="text-xs tracking-wide text-fg/60">
        {event.kind} · {new Date(event.at).toLocaleString()} · {event.actor}
      </p>
      <p className="mt-1 text-sm text-fg">{event.message}</p>
    </li>
  )
}
