import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Plus } from "lucide-react"

import { engagementsApi } from "@/api/endpoints/engagements"
import { EngagementStatus } from "@/types/enums"

export const Route = createFileRoute("/engagements/")({
  component: EngagementsListPage,
})

function statusBadgeClass(status: EngagementStatus): string {
  switch (status) {
    case EngagementStatus.ACTIVE:
      return "border-primary/40 bg-primary/10 text-primary"
    case EngagementStatus.SCOPING:
      return "border-fg/30 bg-neutral-50 text-fg"
    case EngagementStatus.DELIVERED:
      return "border-stone/40 bg-danger/10 text-fg"
    case EngagementStatus.CLOSED:
      return "border-fg/20 bg-white text-fg/60"
    case EngagementStatus.CANCELLED:
      return "border-danger-soft/40 bg-danger-soft/10 text-danger-soft"
    default:
      return "border-fg/30 bg-white text-fg"
  }
}

/**
 * `true` when the engagement's due date has passed but it is not yet delivered/closed.
 * Drives the inline yellow indicator in the list.
 */
function isOverdue(due: string | null | undefined, status: EngagementStatus): boolean {
  if (!due) return false
  if (status === EngagementStatus.DELIVERED || status === EngagementStatus.CLOSED) return false
  if (status === EngagementStatus.CANCELLED) return false
  return Date.parse(due) < Date.now()
}

function EngagementsListPage() {
  const query = useQuery({
    queryKey: ["engagements", "list"],
    queryFn: () => engagementsApi.list(),
    staleTime: 30_000,
  })
  const items = query.data?.items ?? []

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl space-y-4">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-fg">Engagements</h1>
            <p className="mt-1 text-sm text-fg/70">
              Consultancy work — policy drafts, training, audits, advisory. Tracks scope,
              deliverables, and hours-logged.
            </p>
          </div>
          <Link
            to="/engagements/new"
            className="inline-flex h-9 items-center gap-1.5 px-4 bg-primary text-white font-medium rounded-none hover:bg-primary"
          >
            <Plus className="h-4 w-4" />
            New engagement
          </Link>
        </header>

        {query.isPending ? (
          <p className="text-sm text-fg/60">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-fg/60">No engagements yet.</p>
        ) : (
          <ul className="divide-y divide-ink/10 border border-fg/20 bg-white">
            {items.map((e) => {
              const overdue = isOverdue(e.due_date, e.status)
              const budgetPct = e.budget_hours
                ? Math.round((e.hours_logged / e.budget_hours) * 100)
                : null
              return (
                <li key={e.id} className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <Link
                        to="/engagements/$engagementId"
                        params={{ engagementId: e.id }}
                        className="text-sm font-semibold text-fg hover:text-primary hover:underline"
                      >
                        {e.name}
                      </Link>
                      <p className="mt-1 text-xs text-fg/60">
                        {e.engagement_type} · started{" "}
                        {new Date(e.start_date).toLocaleDateString()}
                        {e.due_date
                          ? ` · due ${new Date(e.due_date).toLocaleDateString()}`
                          : ""}
                        {overdue && (
                          <span className="ml-2 border border-amber-500/40 bg-amber-50 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-700">
                            Overdue
                          </span>
                        )}
                      </p>
                      {e.description ? (
                        <p className="mt-1 text-sm text-fg/70 line-clamp-2">{e.description}</p>
                      ) : null}
                      <p className="mt-2 text-xs text-fg/60">
                        Hours: {e.hours_logged}
                        {e.budget_hours ? ` / ${e.budget_hours} (${budgetPct}%)` : ""}
                      </p>
                    </div>
                    <span
                      className={`shrink-0 border px-2 py-0.5 text-[11px] uppercase tracking-wide ${statusBadgeClass(e.status)}`}
                    >
                      {e.status}
                    </span>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
