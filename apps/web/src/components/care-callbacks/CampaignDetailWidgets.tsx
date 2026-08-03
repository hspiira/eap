import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ChevronRight,
  Phone,
  ShieldCheck,
} from "lucide-react"

import { K_ANON_FLOOR } from "@/api/endpoints/care-callbacks-fixture"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  RailSection,
  Stat,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { nameInitials } from "@/lib/display"
import { cn } from "@/lib/utils"
import { CampaignStatusPill } from "@/routes/care-callbacks/index"
import type {
  CallbackCampaign,
  CallbackCampaignAggregate,
  CallbackCase,
  Client,
} from "@/types/entities"
import { CallbackCaseStatus } from "@/types/enums"

export function Hero({
  campaign,
  client,
}: {
  campaign: CallbackCampaign
  client: Client | null
}) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <Phone className="size-4" />
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {campaign.name}
      </h1>
      {client ? (
        <Link
          to="/clients/$clientId"
          params={{ clientId: client.id }}
          className="text-xs text-fg/65 hover:text-primary"
        >
          {client.name}
          <span className="ml-1.5 font-mono text-fg/45">{client.code}</span>
        </Link>
      ) : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <CampaignStatusPill status={campaign.status} />
    </div>
  )
}

export function CasesPanel({
  cases,
  loading,
}: {
  cases: CallbackCase[]
  loading: boolean
}) {
  if (loading) return <p className="text-sm text-fg/65">Loading cases…</p>
  if (cases.length === 0) {
    return (
      <EmptyState
        title="No cases generated yet"
        description="Cases are seeded into counsellor worklists when the campaign is activated."
      />
    )
  }
  return (
    <div className="overflow-hidden border border-fg/10 bg-surface">
      <Table className="w-full caption-bottom text-sm">
        <TableHeader className="border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
          <TableRow className="border-fg/8 hover:bg-transparent">
            <TableHead>Person</TableHead>
            <TableHead>Assigned</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-fg/65">Attempts</TableHead>
            <TableHead className="w-10 text-right text-fg/65">
              <span className="sr-only">Open</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {cases.map((c) => (
            <TableRow key={c.id} className="group border-fg/8">
              <TableCell>
                <Link
                  to="/care-callbacks/worklist/$caseId"
                  params={{ caseId: c.id }}
                  className="text-sm font-medium text-fg group-hover:text-primary"
                >
                  {c.person_display_name}
                </Link>
              </TableCell>
              <TableCell>
                <Link
                  to="/users/$userId"
                  params={{ userId: c.assigned_user_id }}
                  className="font-mono text-xs text-fg/75 hover:text-primary"
                >
                  {c.assigned_user_id}
                </Link>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-1.5">
                  <CaseStatusPill status={c.status} />
                  {c.crisis_flagged ? (
                    <span
                      className="inline-flex items-center gap-1 rounded-sm border border-danger/30 bg-danger-soft px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-danger-fg"
                      title="Crisis protocol invoked"
                    >
                      <AlertTriangle className="size-3" />
                      Crisis
                    </span>
                  ) : null}
                </div>
              </TableCell>
              <TableCell className="font-mono text-xs text-fg/75">
                {c.attempt_count}
              </TableCell>
              <TableCell className="text-right">
                <Link
                  to="/care-callbacks/worklist/$caseId"
                  params={{ caseId: c.id }}
                  aria-label="Open case"
                  className="inline-grid size-7 place-items-center rounded-sm text-fg/55 hover:bg-surface-hover hover:text-fg"
                >
                  <ChevronRight className="size-3.5" />
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export function AggregatePanel({
  aggregate,
  loading,
}: {
  aggregate: CallbackCampaignAggregate | null
  loading: boolean
}) {
  if (loading) return <p className="text-sm text-fg/65">Computing aggregate…</p>
  if (!aggregate) {
    return (
      <EmptyState
        title="Aggregate unavailable"
        description="Try again once the campaign has produced outcomes."
      />
    )
  }
  if (!aggregate.k_floor_met) {
    return (
      <DetailCard title="Aggregate report (no PII)">
        <div className="flex items-start gap-2.5">
          <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
          <div className="min-w-0 flex-1 text-sm">
            <p className="font-medium text-fg">Insufficient data</p>
            <p className="mt-0.5 text-fg/60">
              Aggregate metrics are suppressed until at least {K_ANON_FLOOR} cases are
              completed (k-anon floor). Currently {aggregate.cases_completed} completed.
            </p>
          </div>
        </div>
      </DetailCard>
    )
  }
  return (
    <div className="space-y-4">
      <DetailCard title="Counts">
        <DetailGrid>
          <DetailRow label="Cases total" value={aggregate.cases_total} />
          <DetailRow label="Completed" value={aggregate.cases_completed} />
          <DetailRow label="No answer" value={aggregate.cases_no_answer} />
          <DetailRow label="Declined" value={aggregate.cases_declined} />
          <DetailRow label="Crisis" value={aggregate.cases_crisis} />
          {aggregate.wos5_delta_mean != null ? (
            <DetailRow
              label="WOS-5 post mean"
              value={aggregate.wos5_delta_mean.toFixed(2)}
            />
          ) : null}
        </DetailGrid>
      </DetailCard>

      <DetailCard title="Question summaries">
        <Table className="w-full text-sm">
          <TableHeader>
            <TableRow className="text-fg/65 hover:bg-transparent">
              <TableHead className="px-2 py-1.5 text-xs font-medium tracking-wide">
                Question
              </TableHead>
              <TableHead className="px-2 py-1.5 text-right text-xs font-medium tracking-wide">
                n
              </TableHead>
              <TableHead className="px-2 py-1.5 text-right text-xs font-medium tracking-wide">
                Mean / Top
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {aggregate.question_summaries.map((s) => (
              <TableRow key={s.question_key} className="border-fg/8">
                <TableCell className="px-2 py-1.5">{s.prompt}</TableCell>
                <TableCell className="px-2 py-1.5 text-right font-mono">
                  {s.n}
                </TableCell>
                <TableCell className="px-2 py-1.5 text-right font-mono">
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
      </DetailCard>
    </div>
  )
}

export function DetailRail({
  campaign,
  client,
  completionPct,
  crisisCount,
}: {
  campaign: CallbackCampaign
  client: Client | null
  completionPct: number
  crisisCount: number
}) {
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Cases" value={campaign.case_count} />
          <Stat
            label="Done"
            value={`${completionPct}%`}
          />
          <Stat label="In progress" value={campaign.cases_in_progress} />
          <Stat
            label="Crisis"
            value={
              crisisCount > 0 ? (
                <span className="text-danger-fg">{crisisCount}</span>
              ) : (
                "0"
              )
            }
          />
        </div>
      </RailSection>

      {client ? (
        <RailSection title="Client">
          <Link
            to="/clients/$clientId"
            params={{ clientId: client.id }}
            className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
          >
            <span
              aria-hidden
              className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
            >
              {nameInitials(client.name)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-fg">{client.name}</p>
              <p className="truncate font-mono text-[11px] text-fg/55">{client.code}</p>
            </div>
          </Link>
        </RailSection>
      ) : null}

      <RailSection title="Privacy">
        <p className="rounded-sm border border-fg/10 bg-surface px-3 py-2 text-xs text-fg/65">
          <ShieldCheck className="mr-1 inline size-3 text-primary" />
          Aggregate report suppresses metrics until at least {K_ANON_FLOOR} cases
          complete (k-anon floor).
        </p>
      </RailSection>
    </div>
  )
}

export function CaseStatusPill({ status }: { status: CallbackCaseStatus }) {
  const tone =
    status === CallbackCaseStatus.CRISIS_ESCALATED
      ? "border-danger/30 bg-danger-soft text-danger-fg"
      : status === CallbackCaseStatus.COMPLETED
        ? "border-primary/30 bg-primary/10 text-primary"
        : "border-fg/15 bg-bg text-fg/75"
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

function topHistogramEntry(h: Record<string, number>): string {
  const entries = Object.entries(h)
  if (entries.length === 0) return "—"
  entries.sort((a, b) => b[1] - a[1])
  const [value, count] = entries[0]
  return `${value} (${count})`
}
