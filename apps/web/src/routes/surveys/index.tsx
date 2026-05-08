import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Plus } from "lucide-react"

import { surveysApi } from "@/api/endpoints/surveys"
import { SurveyStatus } from "@/types/enums"

export const Route = createFileRoute("/surveys/")({
  component: SurveysListPage,
})

function statusBadgeClass(status: SurveyStatus): string {
  switch (status) {
    case SurveyStatus.COLLECTING:
      return "border-primary/40 bg-primary/10 text-primary"
    case SurveyStatus.DRAFT:
      return "border-fg/30 bg-neutral-50 text-fg"
    case SurveyStatus.CLOSED:
      return "border-fg/20 bg-white text-fg/60"
    default:
      return "border-fg/30 bg-white text-fg"
  }
}

function SurveysListPage() {
  const query = useQuery({
    queryKey: ["surveys", "list"],
    queryFn: () => surveysApi.list(),
    staleTime: 30_000,
  })
  const items = query.data?.items ?? []

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl space-y-4">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-fg">Surveys</h1>
            <p className="mt-1 text-sm text-fg/70">
              Anonymous post-engagement surveys hosted on Google Forms (or similar). Responses
              stream into Evexía via webhook; aggregates respect a k-anon floor.
            </p>
          </div>
          <Link
            to="/surveys/new"
            className="inline-flex h-9 items-center gap-1.5 px-4 bg-primary text-white font-medium rounded-none hover:bg-primary"
          >
            <Plus className="h-4 w-4" />
            New survey
          </Link>
        </header>

        {query.isPending ? (
          <p className="text-sm text-fg/60">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-fg/60">No surveys yet.</p>
        ) : (
          <ul className="divide-y divide-ink/10 border border-fg/20 bg-white">
            {items.map((s) => (
              <li key={s.id} className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <Link
                      to="/surveys/$surveyId"
                      params={{ surveyId: s.id }}
                      className="text-sm font-semibold text-fg hover:text-primary hover:underline"
                    >
                      {s.name}
                    </Link>
                    <p className="mt-1 text-xs text-fg/60">
                      {new Date(s.period_start).toLocaleDateString()} –{" "}
                      {new Date(s.period_end).toLocaleDateString()} · source: {s.source} ·{" "}
                      {s.response_count} response(s)
                    </p>
                    {s.description ? (
                      <p className="mt-1 text-sm text-fg/70 line-clamp-2">{s.description}</p>
                    ) : null}
                  </div>
                  <span
                    className={`shrink-0 border px-2 py-0.5 text-[11px] uppercase tracking-wide ${statusBadgeClass(s.status)}`}
                  >
                    {s.status}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
