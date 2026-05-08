import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, Printer } from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { K_ANON_FLOOR } from "@/api/endpoints/care-callbacks-fixture"
import { Button } from "@/components/ui/button"

import { type RenewalPackData,renewalPackFixture } from "./renewal-pack-fixture"

export const Route = createFileRoute("/reports/$templateSlug")({
  component: ReportTemplatePage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { client_id?: string; campaign_id?: string } = {}
    if (typeof search.client_id === "string" && search.client_id.trim()) {
      out.client_id = search.client_id
    }
    if (typeof search.campaign_id === "string" && search.campaign_id.trim()) {
      out.campaign_id = search.campaign_id
    }
    return out
  },
})

function ReportTemplatePage() {
  const { templateSlug } = Route.useParams()

  if (templateSlug === "per-client-renewal") return <PerClientRenewalPack />
  if (templateSlug === "care-callback-summary") return <CareCallbackWaveSummary />
  return <UnknownTemplate slug={templateSlug} />
}

function PerClientRenewalPack() {
  const [data] = useState<RenewalPackData>(renewalPackFixture)

  const handlePrint = () => {
    if (typeof window !== "undefined") window.print()
  }

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6 print:p-0">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-4 print:hidden">
          <div className="flex items-center gap-3">
            <Link
              to="/reports"
              className="inline-flex h-9 items-center gap-1.5 px-2 text-sm text-fg/70 hover:text-fg"
            >
              <ArrowLeft className="h-4 w-4" />
              Reports
            </Link>
            <h1 className="text-xl font-semibold text-fg">Renewal pack — {data.client.name}</h1>
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="rounded-none border-fg/30 text-fg"
            onClick={handlePrint}
          >
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
        </header>

        <article className="space-y-8 border border-fg/20 bg-white p-8 print:border-0 print:p-0">
          <RenewalPackHeader data={data} />
          <SessionsByMonth data={data} />
          <DiagnosisPrevalence data={data} />
          <CareCallbackOutcomes data={data} />
          <SatisfactionDistribution data={data} />
        </article>
      </div>
    </div>
  )
}

function RenewalPackHeader({ data }: { data: RenewalPackData }) {
  return (
    <section>
      <p className="text-xs uppercase tracking-wide text-fg/60">Renewal pack</p>
      <h2 className="mt-1 text-2xl font-semibold text-fg">{data.client.name}</h2>
      <dl className="mt-4 grid gap-4 sm:grid-cols-3">
        <div>
          <dt className="text-xs text-fg/60">Period</dt>
          <dd className="text-sm text-fg">{data.period}</dd>
        </div>
        <div>
          <dt className="text-xs text-fg/60">Tier</dt>
          <dd className="text-sm text-fg">Tier {data.client.tier}</dd>
        </div>
        <div>
          <dt className="text-xs text-fg/60">Active employees</dt>
          <dd className="text-sm text-fg">{data.activeEmployees.toLocaleString()}</dd>
        </div>
      </dl>
    </section>
  )
}

function SessionsByMonth({ data }: { data: RenewalPackData }) {
  const max = Math.max(...data.sessionsByMonth.map((m) => m.count), 1)
  return (
    <section>
      <h3 className="text-sm font-semibold text-fg">Sessions delivered by month</h3>
      <ul className="mt-3 space-y-2">
        {data.sessionsByMonth.map((m) => (
          <li key={m.month} className="grid grid-cols-[6rem_1fr_3rem] items-center gap-3">
            <span className="text-xs text-fg/70">{m.month}</span>
            <span
              className="block h-2 bg-primary"
              style={{ width: `${Math.round((m.count / max) * 100)}%` }}
              aria-hidden
            />
            <span className="text-right text-xs text-fg">{m.count}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function DiagnosisPrevalence({ data }: { data: RenewalPackData }) {
  const total = data.diagnosisPrevalence.reduce((acc, d) => acc + d.count, 0) || 1
  return (
    <section>
      <h3 className="text-sm font-semibold text-fg">Diagnosis prevalence</h3>
      <ul className="mt-3 space-y-2">
        {data.diagnosisPrevalence.map((d) => {
          const pct = Math.round((d.count / total) * 100)
          return (
            <li key={d.label} className="grid grid-cols-[12rem_1fr_3rem] items-center gap-3">
              <span className="text-xs text-fg/80">{d.label}</span>
              <span
                className="block h-2 bg-danger"
                style={{ width: `${pct}%` }}
                aria-hidden
              />
              <span className="text-right text-xs text-fg">{pct}%</span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

function CareCallbackOutcomes({ data }: { data: RenewalPackData }) {
  return (
    <section>
      <h3 className="text-sm font-semibold text-fg">Care-callback outcomes</h3>
      <table className="mt-3 w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-fg/20 text-left text-xs uppercase text-fg/60">
            <th className="py-2 pr-3 font-medium">Outcome</th>
            <th className="py-2 pr-3 font-medium">Count</th>
            <th className="py-2 font-medium">Share</th>
          </tr>
        </thead>
        <tbody>
          {data.careCallbacks.map((row) => (
            <tr key={row.outcome} className="border-b border-fg/10">
              <td className="py-2 pr-3 text-fg">{row.outcome}</td>
              <td className="py-2 pr-3 text-fg">{row.count}</td>
              <td className="py-2 text-fg/70">{row.share}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function SatisfactionDistribution({ data }: { data: RenewalPackData }) {
  return (
    <section>
      <h3 className="text-sm font-semibold text-fg">Satisfaction distribution</h3>
      <ul className="mt-3 grid grid-cols-5 gap-2 text-center">
        {data.satisfaction.map((s) => (
          <li key={s.bucket} className="border border-fg/20 p-2">
            <div className="text-xs uppercase text-fg/60">{s.bucket}</div>
            <div className="mt-1 text-lg font-semibold text-fg">{s.count}</div>
          </li>
        ))}
      </ul>
    </section>
  )
}

function CareCallbackWaveSummary() {
  const search = Route.useSearch()
  const campaignId = search.campaign_id

  const aggregateQuery = useQuery({
    queryKey: ["care-callback-campaigns", "aggregate", campaignId ?? ""],
    queryFn: () => careCallbacksApi.getAggregate(campaignId as string),
    enabled: !!campaignId,
  })
  const campaignQuery = useQuery({
    queryKey: ["care-callback-campaigns", "detail", campaignId ?? ""],
    queryFn: () => careCallbacksApi.getCampaign(campaignId as string),
    enabled: !!campaignId,
  })

  const handlePrint = () => {
    if (typeof window !== "undefined") window.print()
  }

  if (!campaignId) {
    return (
      <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl space-y-3">
          <h1 className="text-xl font-semibold text-fg">Care callback wave summary</h1>
          <p className="text-sm text-fg/70">
            Pass a <code className="font-mono">?campaign_id=…</code> search param to render the
            summary for a specific wave. From a campaign detail page, use the share-link to
            arrive here pre-populated.
          </p>
          <Link to="/care-callbacks" className="text-sm font-medium text-primary hover:underline">
            ← Pick a campaign
          </Link>
        </div>
      </div>
    )
  }

  const aggregate = aggregateQuery.data
  const campaign = campaignQuery.data

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6 print:p-0">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-4 print:hidden">
          <div className="flex items-center gap-3">
            <Link
              to="/reports"
              className="inline-flex h-9 items-center gap-1.5 px-2 text-sm text-fg/70 hover:text-fg"
            >
              <ArrowLeft className="h-4 w-4" />
              Reports
            </Link>
            <h1 className="text-xl font-semibold text-fg">
              Wave summary{campaign ? ` — ${campaign.name}` : ""}
            </h1>
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="rounded-none border-fg/30 text-fg"
            onClick={handlePrint}
          >
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
        </header>

        <article className="space-y-8 border border-fg/20 bg-white p-8 print:border-0 print:p-0">
          {aggregateQuery.isPending || campaignQuery.isPending ? (
            <p className="text-sm text-fg/60">Loading…</p>
          ) : !aggregate || !campaign ? (
            <p className="text-sm text-fg/60">Aggregate unavailable for this campaign.</p>
          ) : (
            <>
              <section>
                <p className="text-xs uppercase tracking-wide text-fg/60">Wave summary</p>
                <h2 className="mt-1 text-2xl font-semibold text-fg">{campaign.name}</h2>
                <dl className="mt-4 grid gap-4 sm:grid-cols-3">
                  <div>
                    <dt className="text-xs text-fg/60">Period</dt>
                    <dd className="text-sm text-fg">
                      {new Date(campaign.period_start).toLocaleDateString()} –{" "}
                      {new Date(campaign.period_end).toLocaleDateString()}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-fg/60">Status</dt>
                    <dd className="text-sm text-fg">{campaign.status}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-fg/60">Counsellors</dt>
                    <dd className="text-sm text-fg">{campaign.counsellor_user_ids.length}</dd>
                  </div>
                </dl>
              </section>

              <section className="grid gap-3 sm:grid-cols-5">
                <Stat label="Cases" value={aggregate.cases_total} />
                <Stat label="Completed" value={aggregate.cases_completed} />
                <Stat label="No answer" value={aggregate.cases_no_answer} />
                <Stat label="Declined" value={aggregate.cases_declined} />
                <Stat label="Crisis" value={aggregate.cases_crisis} highlight />
              </section>

              {!aggregate.k_floor_met ? (
                <p className="text-sm text-fg/70">
                  <strong>Insufficient data.</strong> Aggregate metrics suppressed until at least{" "}
                  {K_ANON_FLOOR} cases are completed.
                </p>
              ) : (
                <section>
                  <h3 className="text-sm font-semibold text-fg">Per-question outcomes</h3>
                  <p className="mt-1 text-xs text-fg/60">
                    {aggregate.wos5_delta_mean !== null
                      ? `WOS-5 post mean: ${aggregate.wos5_delta_mean}`
                      : "WOS-5 follow-up not collected for this wave."}
                  </p>
                  <table className="mt-3 w-full border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-fg/20 text-left text-xs uppercase text-fg/60">
                        <th className="py-2 pr-3 font-medium">Question</th>
                        <th className="py-2 pr-3 font-medium">n</th>
                        <th className="py-2 font-medium">Mean / Top</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aggregate.question_summaries.map((s) => (
                        <tr key={s.question_key} className="border-b border-fg/10">
                          <td className="py-2 pr-3 text-fg">{s.prompt}</td>
                          <td className="py-2 pr-3 text-fg">{s.n}</td>
                          <td className="py-2 text-fg/70">
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
                </section>
              )}
            </>
          )}
        </article>
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
  value: number
  highlight?: boolean
}) {
  return (
    <div
      className={`border p-3 ${
        highlight ? "border-danger-soft/40 bg-danger-soft/10" : "border-fg/20"
      }`}
    >
      <div className="text-xs uppercase text-fg/60">{label}</div>
      <div
        className={`mt-1 text-lg font-semibold ${highlight ? "text-danger-soft" : "text-fg"}`}
      >
        {value}
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

function UnknownTemplate({ slug }: { slug: string }) {
  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-3xl space-y-3">
        <h1 className="text-xl font-semibold text-fg">Template not available</h1>
        <p className="text-sm text-fg/70">
          The template <span className="font-mono text-fg">{slug}</span> isn&apos;t implemented yet.
          Phase 3 will ship the wave-summary, tier-portfolio, and anchor-cohort templates.
        </p>
        <Link to="/reports" className="text-sm font-medium text-primary hover:underline">
          ← Back to reports
        </Link>
      </div>
    </div>
  )
}
