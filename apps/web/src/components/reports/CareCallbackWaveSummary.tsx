
import {
  ShieldCheck,
} from "lucide-react"

import { K_ANON_FLOOR } from "@/api/endpoints/care-callbacks-fixture"
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


function topHistogramEntry(h: Record<string, number>): string {
  const entries = Object.entries(h)
  if (entries.length === 0) return "—"
  entries.sort((a, b) => b[1] - a[1])
  const [value, count] = entries[0]
  return `${value} (${count})`
}


import { Field, ReportSection, SummaryStat } from "@/components/reports/ReportShared"


export function WaveSummaryBody({
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
        <p className="text-[11px] font-semibold tracking-wide text-fg/55">
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

export function CampaignStatusPill({ status }: { status: CallbackCampaignStatus }) {
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
