import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowLeft,
  FileBarChart,
  FileText,
  PieChart,
  Printer,
  ShieldCheck,
} from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { K_ANON_FLOOR } from "@/api/endpoints/care-callbacks-fixture"
import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import type { CallbackCampaign, CallbackCampaignAggregate } from "@/types/entities"
import { CallbackCampaignStatus } from "@/types/enums"

import { type RenewalPackData, renewalPackFixture } from "./renewal-pack-fixture"

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

// ─────────────────────────────────────────────────────────────────────────────
// Per-client renewal pack
// ─────────────────────────────────────────────────────────────────────────────

function PerClientRenewalPack() {
  const [data] = useState<RenewalPackData>(renewalPackFixture)
  const handlePrint = () => {
    if (typeof window !== "undefined") window.print()
  }

  return (
    <PageShell
      icon={FileText}
      breadcrumb={`Reports · Renewal pack · ${data.client.name}`}
      actions={
        <>
          <BackLink />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 px-2.5"
            onClick={handlePrint}
          >
            <Printer className="size-3.5" />
            Print
          </Button>
        </>
      }
    >
      <div className="min-h-0 flex-1 overflow-y-auto bg-bg print:overflow-visible">
        <div className="mx-auto max-w-4xl px-5 py-6 print:px-0 print:py-0">
          <article
            className={cn(
              "space-y-8 rounded-sm border border-fg/10 bg-surface p-8",
              "print:border-0 print:bg-white print:p-0 print:text-black",
            )}
          >
            <RenewalPackHeader data={data} />
            <SessionsByMonth data={data} />
            <DiagnosisPrevalence data={data} />
            <CareCallbackOutcomes data={data} />
            <SatisfactionDistribution data={data} />
          </article>
        </div>
      </div>
    </PageShell>
  )
}

function RenewalPackHeader({ data }: { data: RenewalPackData }) {
  return (
    <section>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-fg/55">
        Renewal pack
      </p>
      <h2 className="mt-1 text-2xl font-semibold text-fg">{data.client.name}</h2>
      <dl className="mt-4 grid gap-4 sm:grid-cols-3">
        <Field label="Period" value={data.period} />
        <Field label="Tier" value={`Tier ${data.client.tier}`} />
        <Field
          label="Active employees"
          value={data.activeEmployees.toLocaleString()}
        />
      </dl>
    </section>
  )
}

function SessionsByMonth({ data }: { data: RenewalPackData }) {
  const max = Math.max(...data.sessionsByMonth.map((m) => m.count), 1)
  return (
    <ReportSection title="Sessions delivered by month">
      <ul className="mt-3 space-y-2">
        {data.sessionsByMonth.map((m) => (
          <li
            key={m.month}
            className="grid grid-cols-[6rem_1fr_3rem] items-center gap-3"
          >
            <span className="text-xs text-fg/65">{m.month}</span>
            <span className="block h-2 rounded-sm bg-fg/8" aria-hidden>
              <span
                className="block h-full bg-primary"
                style={{ width: `${Math.round((m.count / max) * 100)}%` }}
              />
            </span>
            <span className="text-right font-mono text-xs text-fg">{m.count}</span>
          </li>
        ))}
      </ul>
    </ReportSection>
  )
}

function DiagnosisPrevalence({ data }: { data: RenewalPackData }) {
  const total = data.diagnosisPrevalence.reduce((acc, d) => acc + d.count, 0) || 1
  return (
    <ReportSection title="Diagnosis prevalence">
      <ul className="mt-3 space-y-2">
        {data.diagnosisPrevalence.map((d) => {
          const pct = Math.round((d.count / total) * 100)
          return (
            <li
              key={d.label}
              className="grid grid-cols-[12rem_1fr_3rem] items-center gap-3"
            >
              <span className="text-xs text-fg/80">{d.label}</span>
              <span className="block h-2 rounded-sm bg-fg/8" aria-hidden>
                <span
                  className="block h-full bg-danger"
                  style={{ width: `${pct}%` }}
                />
              </span>
              <span className="text-right font-mono text-xs text-fg">{pct}%</span>
            </li>
          )
        })}
      </ul>
    </ReportSection>
  )
}

function CareCallbackOutcomes({ data }: { data: RenewalPackData }) {
  return (
    <ReportSection title="Care-callback outcomes">
      <Table className="mt-3 w-full border-collapse text-sm">
        <TableHeader>
          <TableRow className="border-fg/15 text-left hover:bg-transparent">
            <TableHead className="py-2 pr-3 text-[11px] font-semibold tracking-wide">Outcome</TableHead>
            <TableHead className="py-2 pr-3 text-[11px] font-semibold tracking-wide">Count</TableHead>
            <TableHead className="py-2 text-[11px] font-semibold tracking-wide">Share</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.careCallbacks.map((row) => (
            <TableRow key={row.outcome} className="border-fg/10">
              <TableCell className="py-2 pr-3 text-fg">{row.outcome}</TableCell>
              <TableCell className="py-2 pr-3 font-mono text-fg">{row.count}</TableCell>
              <TableCell className="py-2 font-mono text-fg/65">{row.share}%</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </ReportSection>
  )
}

function SatisfactionDistribution({ data }: { data: RenewalPackData }) {
  return (
    <ReportSection title="Satisfaction distribution">
      <ul className="mt-3 grid grid-cols-5 gap-2 text-center">
        {data.satisfaction.map((s) => (
          <li
            key={s.bucket}
            className="rounded-sm border border-fg/15 bg-bg p-2 print:bg-white"
          >
            <div className="text-[10px] font-semibold uppercase tracking-wide text-fg/55">
              {s.bucket}
            </div>
            <div className="mt-1 font-mono text-lg font-semibold text-fg">{s.count}</div>
          </li>
        ))}
      </ul>
    </ReportSection>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Care callback wave summary
// ─────────────────────────────────────────────────────────────────────────────

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
      <PageShell icon={PieChart} breadcrumb="Reports · Wave summary">
        <EmptyState
          icon={PieChart}
          title="Pick a campaign"
          description="The wave summary is rendered for one campaign. Open it from the campaign detail page or pass a campaign_id query parameter."
          action={
            <Link
              to="/care-callbacks"
              className="inline-flex h-9 items-center gap-1.5 rounded-sm border border-fg/15 bg-surface px-3 text-sm font-medium text-fg hover:bg-surface-hover"
            >
              <ArrowLeft className="size-4" />
              Pick a campaign
            </Link>
          }
        />
      </PageShell>
    )
  }

  const aggregate = aggregateQuery.data
  const campaign = campaignQuery.data
  const loading = aggregateQuery.isPending || campaignQuery.isPending
  const breadcrumbName = campaign ? campaign.name : "…"

  return (
    <PageShell
      icon={PieChart}
      breadcrumb={`Reports · Wave summary · ${breadcrumbName}`}
      actions={
        <>
          <BackLink />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 px-2.5"
            onClick={handlePrint}
            disabled={loading || !campaign || !aggregate}
          >
            <Printer className="size-3.5" />
            Print
          </Button>
        </>
      }
    >
      <div className="min-h-0 flex-1 overflow-y-auto bg-bg print:overflow-visible">
        <div className="mx-auto max-w-4xl px-5 py-6 print:px-0 print:py-0">
          <article
            className={cn(
              "space-y-8 rounded-sm border border-fg/10 bg-surface p-8",
              "print:border-0 print:bg-white print:p-0 print:text-black",
            )}
          >
            {loading ? (
              <p className="text-sm text-fg/65">Loading wave aggregate…</p>
            ) : !aggregate || !campaign ? (
              <p className="text-sm text-fg/65">Aggregate unavailable for this campaign.</p>
            ) : (
              <WaveSummaryBody campaign={campaign} aggregate={aggregate} />
            )}
          </article>
        </div>
      </div>
    </PageShell>
  )
}

function WaveSummaryBody({
  campaign,
  aggregate,
}: {
  campaign: CallbackCampaign
  aggregate: CallbackCampaignAggregate
}) {
  const completionPct = aggregate.cases_total
    ? Math.round((aggregate.cases_completed / aggregate.cases_total) * 100)
    : 0
  const wos5 = aggregate.wos5_delta_mean
  return (
    <>
      <section>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-fg/55">
          Wave summary
        </p>
        <div className="mt-1 flex flex-wrap items-baseline gap-3">
          <h2 className="text-2xl font-semibold text-fg">{campaign.name}</h2>
          <CampaignStatusPill status={campaign.status} />
        </div>
        {campaign.description ? (
          <p className="mt-2 max-w-2xl text-sm text-fg/65">{campaign.description}</p>
        ) : null}
        <dl className="mt-4 grid gap-4 sm:grid-cols-3">
          <Field
            label="Period"
            value={
              <>
                {new Date(campaign.period_start).toLocaleDateString()}
                <span className="mx-1 text-fg/45">–</span>
                {new Date(campaign.period_end).toLocaleDateString()}
              </>
            }
          />
          <Field
            label="Sampling"
            value={
              <span className="font-mono">
                {campaign.sampling}
                {campaign.sample_size ? ` (n=${campaign.sample_size})` : ""}
              </span>
            }
          />
          <Field label="Counsellors" value={campaign.counsellor_user_ids.length} />
        </dl>
      </section>

      <ReportSection title="Headline counts">
        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-5">
          <SummaryStat label="Cases" value={aggregate.cases_total} />
          <SummaryStat label="Completed" value={aggregate.cases_completed} hint={`${completionPct}%`} />
          <SummaryStat label="No answer" value={aggregate.cases_no_answer} />
          <SummaryStat label="Declined" value={aggregate.cases_declined} />
          <SummaryStat
            label="Crisis"
            value={aggregate.cases_crisis}
            tone={aggregate.cases_crisis > 0 ? "danger" : "default"}
          />
        </div>
      </ReportSection>

      {!aggregate.k_floor_met ? (
        <ReportSection title="Aggregate suppressed">
          <div className="flex items-start gap-2.5 rounded-sm border border-fg/15 bg-bg px-3 py-2.5 print:bg-white">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
            <div className="text-sm">
              <p className="font-medium text-fg">Insufficient data — k-anon floor not met</p>
              <p className="mt-0.5 text-fg/65">
                Per-question metrics are suppressed until at least {K_ANON_FLOOR} cases
                are completed. Currently {aggregate.cases_completed} completed.
              </p>
            </div>
          </div>
        </ReportSection>
      ) : (
        <ReportSection title="Per-question outcomes">
          <p className="mt-1 text-xs text-fg/55">
            {wos5 != null
              ? `WOS-5 follow-up post-mean: ${wos5.toFixed(2)}`
              : "WOS-5 follow-up not collected for this wave."}
          </p>
          <div className="mt-3 overflow-hidden rounded-sm border border-fg/10">
            <Table className="w-full border-collapse text-sm">
              <TableHeader className="bg-bg print:bg-white">
                <TableRow className="text-left hover:bg-transparent">
                  <TableHead className="px-3 py-2 text-[11px] font-semibold tracking-wide">Question</TableHead>
                  <TableHead className="w-16 px-3 py-2 text-right text-[11px] font-semibold tracking-wide">n</TableHead>
                  <TableHead className="w-32 px-3 py-2 text-right text-[11px] font-semibold tracking-wide">
                    Mean / Top
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {aggregate.question_summaries.map((s) => (
                  <TableRow key={s.question_key} className="border-fg/10 last:border-0">
                    <TableCell className="px-3 py-2 text-fg">{s.prompt}</TableCell>
                    <TableCell className="px-3 py-2 text-right font-mono text-fg">{s.n}</TableCell>
                    <TableCell className="px-3 py-2 text-right font-mono text-fg/80">
                      {s.mean !== null && s.mean !== undefined
                        ? s.mean.toFixed(2)
                        : s.histogram
                          ? topHistogramEntry(s.histogram)
                          : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </ReportSection>
      )}

      <ReportSection title="Counsellor pool">
        {campaign.counsellor_user_ids.length === 0 ? (
          <p className="text-xs text-fg/55">No counsellors on this wave.</p>
        ) : (
          <ul className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {campaign.counsellor_user_ids.map((id) => (
              <li
                key={id}
                className="flex items-center gap-2 rounded-sm border border-fg/10 bg-bg px-2.5 py-1.5 print:bg-white"
              >
                <span
                  aria-hidden
                  className="grid size-5 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                >
                  U
                </span>
                <span className="truncate font-mono text-xs text-fg">{id}</span>
              </li>
            ))}
          </ul>
        )}
      </ReportSection>

      <footer className="border-t border-fg/10 pt-4 text-[11px] text-fg/55">
        <ShieldCheck className="mr-1 inline size-3 text-primary" />
        Aggregate report — no PII. Counsellor notes are excluded by design. Generated{" "}
        {new Date().toLocaleString()}.
      </footer>
    </>
  )
}

function CampaignStatusPill({ status }: { status: CallbackCampaignStatus }) {
  const tone =
    status === CallbackCampaignStatus.ACTIVE
      ? "border-primary/30 bg-primary/10 text-primary"
      : status === CallbackCampaignStatus.CANCELLED
        ? "border-danger/30 bg-danger-soft text-danger-fg"
        : status === CallbackCampaignStatus.COMPLETED
          ? "border-fg/15 bg-bg text-fg/65 print:bg-white"
          : "border-fg/20 bg-bg text-fg print:bg-white"
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[11px] font-medium",
        tone,
      )}
    >
      {status}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared bits
// ─────────────────────────────────────────────────────────────────────────────

function ReportSection({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section>
      <h3 className="text-sm font-semibold text-fg">{title}</h3>
      {children}
    </section>
  )
}

function Field({
  label,
  value,
}: {
  label: string
  value: React.ReactNode
}) {
  return (
    <div>
      <dt className="text-[11px] font-semibold uppercase tracking-wide text-fg/55">
        {label}
      </dt>
      <dd className="mt-0.5 text-sm text-fg">{value}</dd>
    </div>
  )
}

function SummaryStat({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string
  value: number
  hint?: string
  tone?: "default" | "danger"
}) {
  const isDanger = tone === "danger"
  return (
    <div
      className={cn(
        "rounded-sm border bg-bg px-3 py-2 print:bg-white",
        isDanger ? "border-danger/30 bg-danger-soft" : "border-fg/15",
      )}
    >
      <div
        className={cn(
          "flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide",
          isDanger ? "text-danger-fg" : "text-fg/55",
        )}
      >
        {isDanger ? <AlertTriangle className="size-3" /> : null}
        {label}
      </div>
      <div className="mt-0.5 flex items-baseline gap-2">
        <span
          className={cn(
            "font-mono text-lg font-semibold",
            isDanger ? "text-danger-fg" : "text-fg",
          )}
        >
          {value}
        </span>
        {hint ? (
          <span className="font-mono text-[11px] text-fg/55">{hint}</span>
        ) : null}
      </div>
    </div>
  )
}

function BackLink() {
  return (
    <Link
      to="/reports"
      className="inline-flex h-7 items-center gap-1 rounded-sm px-2 text-xs text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
    >
      <ArrowLeft className="size-3.5" />
      Reports
    </Link>
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
    <PageShell icon={FileBarChart} breadcrumb={`Reports · ${slug}`}>
      <EmptyState
        icon={FileBarChart}
        title="Template not available"
        description={
          <>
            The template <span className="font-mono text-fg">{slug}</span> isn&apos;t
            implemented yet. Phase 3 will ship the wave-summary, tier-portfolio, and
            anchor-cohort templates.
          </>
        }
        action={
          <Link
            to="/reports"
            className="inline-flex h-9 items-center gap-1.5 rounded-sm border border-fg/15 bg-surface px-3 text-sm font-medium text-fg hover:bg-surface-hover"
          >
            <ArrowLeft className="size-4" />
            Back to reports
          </Link>
        }
      />
    </PageShell>
  )
}
