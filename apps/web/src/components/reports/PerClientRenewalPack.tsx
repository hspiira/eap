import { useState } from "react"

import {
  FileText,
  Printer,
} from "lucide-react"

import { PageShell } from "@/components/common/PageShell"
import { BackLink, Field, ReportSection } from "@/components/reports/ReportShared"
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
import { type RenewalPackData, renewalPackFixture } from "@/routes/reports/renewal-pack-fixture"


export function PerClientRenewalPack() {
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

export function RenewalPackHeader({ data }: { data: RenewalPackData }) {
  return (
    <section>
      <p className="text-[11px] font-semibold tracking-wide text-fg/55">
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

export function SessionsByMonth({ data }: { data: RenewalPackData }) {
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

export function DiagnosisPrevalence({ data }: { data: RenewalPackData }) {
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

export function CareCallbackOutcomes({ data }: { data: RenewalPackData }) {
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

export function SatisfactionDistribution({ data }: { data: RenewalPackData }) {
  return (
    <ReportSection title="Satisfaction distribution">
      <ul className="mt-3 grid grid-cols-5 gap-2 text-center">
        {data.satisfaction.map((s) => (
          <li
            key={s.bucket}
            className="rounded-sm border border-fg/15 bg-bg p-2 print:bg-white"
          >
            <div className="text-[10px] font-semibold tracking-wide text-fg/55">
              {s.bucket}
            </div>
            <div className="mt-1 font-mono text-lg font-semibold text-fg">{s.count}</div>
          </li>
        ))}
      </ul>
    </ReportSection>
  )
}
