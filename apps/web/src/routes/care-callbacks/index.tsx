import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Plus } from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { CallbackCampaignStatus } from "@/types/enums"

export const Route = createFileRoute("/care-callbacks/")({
  component: CampaignsListPage,
})

function statusBadgeClass(status: CallbackCampaignStatus): string {
  switch (status) {
    case CallbackCampaignStatus.ACTIVE:
      return "border-natural/40 bg-natural/10 text-natural-dark"
    case CallbackCampaignStatus.SCHEDULED:
      return "border-ink/30 bg-neutral-50 text-ink"
    case CallbackCampaignStatus.COMPLETED:
      return "border-ink/20 bg-white text-ink/60"
    case CallbackCampaignStatus.CANCELLED:
      return "border-danger-soft/40 bg-danger-soft/10 text-danger-soft"
    default:
      return "border-ink/30 bg-white text-ink"
  }
}

function CampaignsListPage() {
  const query = useQuery({
    queryKey: ["care-callback-campaigns", "list"],
    queryFn: () => careCallbacksApi.listCampaigns(),
    staleTime: 30_000,
  })
  const items = query.data?.items ?? []

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl space-y-4">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-ink">Care callback campaigns</h1>
            <p className="mt-1 text-sm text-ink/70">
              Counsellor-initiated wellbeing follow-ups. Audience, sampling, and counsellor pool
              configured per wave.
            </p>
          </div>
          <Link
            to="/care-callbacks/new"
            className="inline-flex h-9 items-center gap-1.5 px-4 bg-natural text-white font-medium rounded-none hover:bg-natural-dark"
          >
            <Plus className="h-4 w-4" />
            New campaign
          </Link>
        </header>

        <nav className="flex gap-3 text-sm text-ink/70">
          <Link
            to="/care-callbacks/worklist"
            className="underline-offset-2 hover:text-natural hover:underline"
          >
            Open my worklist →
          </Link>
        </nav>

        {query.isPending ? (
          <p className="text-sm text-ink/60">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-ink/60">No campaigns yet. Create one to start a wave.</p>
        ) : (
          <ul className="divide-y divide-ink/10 border border-ink/20 bg-white">
            {items.map((c) => {
              const completionPct = c.case_count
                ? Math.round((c.cases_completed / c.case_count) * 100)
                : 0
              return (
                <li key={c.id} className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <Link
                        to="/care-callbacks/$campaignId"
                        params={{ campaignId: c.id }}
                        className="text-sm font-semibold text-ink hover:text-natural hover:underline"
                      >
                        {c.name}
                      </Link>
                      <p className="mt-1 text-xs text-ink/60">
                        {new Date(c.period_start).toLocaleDateString()} –{" "}
                        {new Date(c.period_end).toLocaleDateString()} · sampling: {c.sampling}
                        {c.sample_size ? ` (n=${c.sample_size})` : ""} ·{" "}
                        {c.counsellor_user_ids.length} counsellor(s)
                      </p>
                      {c.description ? (
                        <p className="mt-1 text-sm text-ink/70 line-clamp-2">{c.description}</p>
                      ) : null}
                      <p className="mt-2 text-xs text-ink/60">
                        Cases: {c.cases_completed}/{c.case_count} completed · {c.cases_in_progress} in
                        progress · {completionPct}%
                      </p>
                    </div>
                    <span
                      className={`shrink-0 border px-2 py-0.5 text-[11px] uppercase tracking-wide ${statusBadgeClass(c.status)}`}
                    >
                      {c.status}
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
