import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { AlertTriangle, ShieldCheck } from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { K_ANON_FLOOR } from "@/api/endpoints/care-callbacks-fixture"

export const Route = createFileRoute("/care-callbacks/$campaignId")({
  component: CampaignDetailPage,
})

function CampaignDetailPage() {
  const { campaignId } = Route.useParams()
  const campaignQuery = useQuery({
    queryKey: ["care-callback-campaigns", "detail", campaignId],
    queryFn: () => careCallbacksApi.getCampaign(campaignId),
  })
  const casesQuery = useQuery({
    queryKey: ["care-callback-cases", "list", { campaign_id: campaignId }],
    queryFn: () => careCallbacksApi.listCases({ campaign_id: campaignId }),
  })
  const aggregateQuery = useQuery({
    queryKey: ["care-callback-campaigns", "aggregate", campaignId],
    queryFn: () => careCallbacksApi.getAggregate(campaignId),
  })

  if (campaignQuery.isPending) {
    return <p className="p-6 text-sm text-ink/60">Loading…</p>
  }
  if (!campaignQuery.data) {
    return <p className="p-6 text-sm text-ink/60">Campaign not found.</p>
  }
  const campaign = campaignQuery.data
  const cases = casesQuery.data?.items ?? []
  const aggregate = aggregateQuery.data

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <header>
          <Link
            to="/care-callbacks"
            className="text-xs text-ink/60 hover:text-natural hover:underline"
          >
            ← All campaigns
          </Link>
          <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold text-ink">{campaign.name}</h1>
              <p className="mt-1 text-sm text-ink/70">
                {new Date(campaign.period_start).toLocaleDateString()} –{" "}
                {new Date(campaign.period_end).toLocaleDateString()} · sampling:{" "}
                {campaign.sampling}
                {campaign.sample_size ? ` (n=${campaign.sample_size})` : ""} · status:{" "}
                <span className="font-medium text-ink">{campaign.status}</span>
              </p>
              {campaign.description ? (
                <p className="mt-2 text-sm text-ink/70">{campaign.description}</p>
              ) : null}
            </div>
            <Link
              to="/reports/$templateSlug"
              params={{ templateSlug: "care-callback-summary" }}
              search={{ campaign_id: campaign.id }}
              className="inline-flex h-9 items-center gap-1.5 px-3 border border-ink/30 bg-white text-sm text-ink hover:border-natural hover:text-natural"
            >
              Open wave summary →
            </Link>
          </div>
        </header>

        <section className="border border-ink/20 bg-white p-4">
          <h2 className="text-sm font-semibold text-ink">Cases</h2>
          <p className="mt-1 text-xs text-ink/60">
            {campaign.case_count} total · {campaign.cases_completed} completed ·{" "}
            {campaign.cases_in_progress} in progress
          </p>
          {casesQuery.isPending ? (
            <p className="mt-3 text-sm text-ink/60">Loading cases…</p>
          ) : cases.length === 0 ? (
            <p className="mt-3 text-sm text-ink/60">No cases generated yet.</p>
          ) : (
            <ul className="mt-3 divide-y divide-ink/10 border-t border-ink/10">
              {cases.map((c) => (
                <li key={c.id} className="flex items-center justify-between gap-3 py-2">
                  <div className="min-w-0">
                    <Link
                      to="/care-callbacks/worklist/$caseId"
                      params={{ caseId: c.id }}
                      className="text-sm font-medium text-ink hover:text-natural hover:underline"
                    >
                      {c.person_display_name}
                    </Link>
                    <p className="text-xs text-ink/60">
                      Assigned: {c.assigned_user_id} · attempts: {c.attempt_count}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {c.crisis_flagged && (
                      <span
                        className="inline-flex items-center gap-1 border border-danger-soft/40 bg-danger-soft/10 px-2 py-0.5 text-[11px] uppercase tracking-wide text-danger-soft"
                        title="Crisis protocol invoked"
                      >
                        <AlertTriangle className="h-3 w-3" />
                        Crisis
                      </span>
                    )}
                    <span className="border border-ink/20 bg-neutral-50 px-2 py-0.5 text-[11px] uppercase tracking-wide text-ink">
                      {c.status}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="border border-ink/20 bg-white p-4">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-ink">
            <ShieldCheck className="h-4 w-4 text-natural" /> Aggregate report (no PII)
          </h2>
          {aggregateQuery.isPending ? (
            <p className="mt-2 text-sm text-ink/60">Computing aggregate…</p>
          ) : !aggregate ? (
            <p className="mt-2 text-sm text-ink/60">Aggregate unavailable.</p>
          ) : !aggregate.k_floor_met ? (
            <p className="mt-2 text-sm text-ink/70">
              <strong>Insufficient data.</strong> Aggregate metrics suppressed until at least{" "}
              {K_ANON_FLOOR} cases are completed (k-anon floor). Currently{" "}
              {aggregate.cases_completed} completed.
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              <p className="text-xs text-ink/60">
                {aggregate.cases_total} cases · {aggregate.cases_completed} completed ·{" "}
                {aggregate.cases_no_answer} no-answer · {aggregate.cases_declined} declined ·{" "}
                {aggregate.cases_crisis} crisis-flagged
                {aggregate.wos5_delta_mean !== null
                  ? ` · WOS-5 post mean: ${aggregate.wos5_delta_mean}`
                  : ""}
              </p>
              <table className="w-full border border-ink/10 text-sm">
                <thead className="bg-neutral-50 text-ink">
                  <tr>
                    <th className="border-b border-ink/10 px-2 py-1.5 text-left font-medium">
                      Question
                    </th>
                    <th className="border-b border-ink/10 px-2 py-1.5 text-right font-medium">
                      n
                    </th>
                    <th className="border-b border-ink/10 px-2 py-1.5 text-right font-medium">
                      Mean / Top
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {aggregate.question_summaries.map((s) => (
                    <tr key={s.question_key} className="text-ink/80">
                      <td className="border-b border-ink/10 px-2 py-1.5">{s.prompt}</td>
                      <td className="border-b border-ink/10 px-2 py-1.5 text-right">{s.n}</td>
                      <td className="border-b border-ink/10 px-2 py-1.5 text-right">
                        {s.mean !== null && s.mean !== undefined
                          ? s.mean.toFixed(2)
                          : s.histogram
                            ? topHistogramEntry(s.histogram)
                            : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function topHistogramEntry(h: Record<string, number>): string {
  const entries = Object.entries(h)
  if (entries.length === 0) return "—"
  entries.sort((a, b) => b[1] - a[1])
  const [value, count] = entries[0]
  return `${value} (${count})`
}
