import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Plus } from "lucide-react"

import { incidentsApi } from "@/api/endpoints/incidents"
import { SeverityBadge } from "@/components/common/SeverityBadge"
import { StatusBadge } from "@/components/common/StatusBadge"
import { formatDateTime } from "@/lib/format"

export const Route = createFileRoute("/incidents/")({
  component: IncidentsListPage,
})

function IncidentsListPage() {
  const query = useQuery({
    queryKey: ["incidents", "list"],
    queryFn: () => incidentsApi.list(),
    staleTime: 30_000,
  })
  const items = query.data?.items ?? []

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl space-y-4">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-fg">Critical incidents</h1>
            <p className="mt-1 text-sm text-fg/70">
              CISM log — events, severity, affected population, linked sessions.
            </p>
          </div>
          <Link
            to="/incidents/new"
            className="inline-flex h-9 items-center gap-1.5 px-4 bg-primary text-white font-medium rounded-none hover:bg-primary"
          >
            <Plus className="h-4 w-4" />
            Log incident
          </Link>
        </header>

        {query.isPending ? (
          <p className="text-sm text-fg/60">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-fg/60">No incidents on file.</p>
        ) : (
          <ul className="divide-y divide-ink/10 border border-fg/20 bg-white">
            {items.map((inc) => (
              <li key={inc.id} className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <Link
                      to="/incidents/$incidentId"
                      params={{ incidentId: inc.id }}
                      className="text-sm font-semibold text-fg hover:text-primary hover:underline"
                    >
                      {inc.title}
                    </Link>
                    <p className="mt-1 text-sm text-fg/70 line-clamp-2">{inc.description}</p>
                    <p className="mt-1 text-xs text-fg/60">
                      {formatDateTime(inc.occurred_at)} · {inc.affected_population}{" "}
                      affected · {inc.linked_session_ids?.length ?? 0} session(s) linked
                    </p>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-2">
                    <SeverityBadge severity={inc.severity} />
                    <StatusBadge status={inc.status} />
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
