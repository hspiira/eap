import { useState } from "react"

import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, Printer } from "lucide-react"

import { Button } from "@/components/ui/button"

import { renewalPackFixture, type RenewalPackData } from "./renewal-pack-fixture"

export const Route = createFileRoute("/reports/$templateSlug")({
  component: ReportTemplatePage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { client_id?: string } = {}
    if (typeof search.client_id === "string" && search.client_id.trim()) {
      out.client_id = search.client_id
    }
    return out
  },
})

function ReportTemplatePage() {
  const { templateSlug } = Route.useParams()

  if (templateSlug === "per-client-renewal") return <PerClientRenewalPack />
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
              className="inline-flex h-9 items-center gap-1.5 px-2 text-sm text-ink/70 hover:text-ink"
            >
              <ArrowLeft className="h-4 w-4" />
              Reports
            </Link>
            <h1 className="text-xl font-semibold text-ink">Renewal pack — {data.client.name}</h1>
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="rounded-none border-ink/30 text-ink"
            onClick={handlePrint}
          >
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
        </header>

        <article className="space-y-8 border border-ink/20 bg-white p-8 print:border-0 print:p-0">
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
      <p className="text-xs uppercase tracking-wide text-ink/60">Renewal pack</p>
      <h2 className="mt-1 text-2xl font-semibold text-ink">{data.client.name}</h2>
      <dl className="mt-4 grid gap-4 sm:grid-cols-3">
        <div>
          <dt className="text-xs text-ink/60">Period</dt>
          <dd className="text-sm text-ink">{data.period}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink/60">Tier</dt>
          <dd className="text-sm text-ink">Tier {data.client.tier}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink/60">Active employees</dt>
          <dd className="text-sm text-ink">{data.activeEmployees.toLocaleString()}</dd>
        </div>
      </dl>
    </section>
  )
}

function SessionsByMonth({ data }: { data: RenewalPackData }) {
  const max = Math.max(...data.sessionsByMonth.map((m) => m.count), 1)
  return (
    <section>
      <h3 className="text-sm font-semibold text-ink">Sessions delivered by month</h3>
      <ul className="mt-3 space-y-2">
        {data.sessionsByMonth.map((m) => (
          <li key={m.month} className="grid grid-cols-[6rem_1fr_3rem] items-center gap-3">
            <span className="text-xs text-ink/70">{m.month}</span>
            <span
              className="block h-2 bg-natural"
              style={{ width: `${Math.round((m.count / max) * 100)}%` }}
              aria-hidden
            />
            <span className="text-right text-xs text-ink">{m.count}</span>
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
      <h3 className="text-sm font-semibold text-ink">Diagnosis prevalence</h3>
      <ul className="mt-3 space-y-2">
        {data.diagnosisPrevalence.map((d) => {
          const pct = Math.round((d.count / total) * 100)
          return (
            <li key={d.label} className="grid grid-cols-[12rem_1fr_3rem] items-center gap-3">
              <span className="text-xs text-ink/80">{d.label}</span>
              <span
                className="block h-2 bg-stone"
                style={{ width: `${pct}%` }}
                aria-hidden
              />
              <span className="text-right text-xs text-ink">{pct}%</span>
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
      <h3 className="text-sm font-semibold text-ink">Care-callback outcomes</h3>
      <table className="mt-3 w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-ink/20 text-left text-xs uppercase text-ink/60">
            <th className="py-2 pr-3 font-medium">Outcome</th>
            <th className="py-2 pr-3 font-medium">Count</th>
            <th className="py-2 font-medium">Share</th>
          </tr>
        </thead>
        <tbody>
          {data.careCallbacks.map((row) => (
            <tr key={row.outcome} className="border-b border-ink/10">
              <td className="py-2 pr-3 text-ink">{row.outcome}</td>
              <td className="py-2 pr-3 text-ink">{row.count}</td>
              <td className="py-2 text-ink/70">{row.share}%</td>
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
      <h3 className="text-sm font-semibold text-ink">Satisfaction distribution</h3>
      <ul className="mt-3 grid grid-cols-5 gap-2 text-center">
        {data.satisfaction.map((s) => (
          <li key={s.bucket} className="border border-ink/20 p-2">
            <div className="text-xs uppercase text-ink/60">{s.bucket}</div>
            <div className="mt-1 text-lg font-semibold text-ink">{s.count}</div>
          </li>
        ))}
      </ul>
    </section>
  )
}

function UnknownTemplate({ slug }: { slug: string }) {
  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-3xl space-y-3">
        <h1 className="text-xl font-semibold text-ink">Template not available</h1>
        <p className="text-sm text-ink/70">
          The template <span className="font-mono text-ink">{slug}</span> isn&apos;t implemented yet.
          Phase 3 will ship the wave-summary, tier-portfolio, and anchor-cohort templates.
        </p>
        <Link to="/reports" className="text-sm font-medium text-natural hover:underline">
          ← Back to reports
        </Link>
      </div>
    </div>
  )
}
