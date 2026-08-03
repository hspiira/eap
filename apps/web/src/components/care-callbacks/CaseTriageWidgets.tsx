
import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  Phone,
} from "lucide-react"

import { CrisisAlert } from "@/components/care-callbacks/CrisisAlert"
import {
  DetailCard,
  RailSection,
  Stat,
} from "@/components/common/DetailPrimitives"
import { nameInitials } from "@/lib/display"
import { cn } from "@/lib/utils"
import type { CallbackCase, CallbackOutcome } from "@/types/entities"
import { CallbackCaseStatus } from "@/types/enums"

export function Hero({
  callCase,
  campaignName,
}: {
  callCase: CallbackCase
  campaignName: string | null
}) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 font-mono text-xs font-semibold text-primary"
      >
        {nameInitials(callCase.person_display_name)}
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {callCase.person_display_name}
      </h1>
      {campaignName ? (
        <Link
          to="/care-callbacks/$campaignId"
          params={{ campaignId: callCase.campaign_id }}
          className="text-xs text-fg/65 hover:text-primary"
        >
          {campaignName}
        </Link>
      ) : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <CaseStatusPill status={callCase.status} />
      {callCase.crisis_flagged ? (
        <span className="inline-flex items-center gap-1 rounded-sm border border-danger/30 bg-danger-soft px-1.5 py-0.5 text-[11px] font-medium text-danger-fg">
          <AlertTriangle className="size-3" />
          Crisis
        </span>
      ) : null}
    </div>
  )
}

export function DetailRail({
  callCase,
  campaignId,
  campaignName,
  crisisActive,
}: {
  callCase: CallbackCase
  campaignId: string
  campaignName: string | null
  crisisActive: boolean
}) {
  return (
    <div className="space-y-5">
      <RailSection title="Case state">
        <div className="grid grid-cols-2 gap-3">
          <Stat variant="text" label="Attempts" value={callCase.attempt_count} />
          <Stat variant="text" label="Status" value={<CaseStatusPill status={callCase.status} />} />
          <Stat variant="text"
            label="Started"
            value={
              callCase.started_at
                ? new Date(callCase.started_at).toLocaleDateString()
                : "—"
            }
          />
          <Stat variant="text"
            label="Closed"
            value={
              callCase.closed_at
                ? new Date(callCase.closed_at).toLocaleDateString()
                : "—"
            }
          />
        </div>
      </RailSection>

      <RailSection title="Campaign">
        <Link
          to="/care-callbacks/$campaignId"
          params={{ campaignId }}
          className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
        >
          <span
            aria-hidden
            className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <Phone className="size-3.5" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-fg">
              {campaignName ?? campaignId}
            </p>
            <p className="truncate font-mono text-[11px] text-fg/55">{campaignId}</p>
          </div>
        </Link>
      </RailSection>

      <RailSection title="Subject">
        <Link
          to="/persons/$personId"
          params={{ personId: callCase.person_id }}
          className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-surface px-3 py-2 transition-colors hover:border-fg/25"
        >
          <span
            aria-hidden
            className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
          >
            {nameInitials(callCase.person_display_name)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-fg">
              {callCase.person_display_name}
            </p>
            <p className="truncate font-mono text-[11px] text-fg/55">
              {callCase.person_id.slice(0, 8)}
            </p>
          </div>
        </Link>
      </RailSection>

      {crisisActive ? (
        <RailSection title="Crisis">
          <p className="rounded-sm border border-danger/30 bg-danger-soft px-3 py-2 text-xs text-danger-fg">
            <AlertTriangle className="mr-1 inline size-3" />
            Crisis protocol must be invoked. Submitting will latch this case to{" "}
            <em>Crisis Escalated</em>.
          </p>
        </RailSection>
      ) : null}
    </div>
  )
}

export function ExistingOutcomeCard({ outcome }: { outcome: CallbackOutcome }) {
  return (
    <DetailCard title="Outcome on file">
      <header className="mb-3 flex items-center justify-between gap-2">
        <span className="text-xs text-fg/55">
          {new Date(outcome.recorded_at).toLocaleString()} · by{" "}
          <span className="font-mono">{outcome.recorded_by_user_id}</span>
        </span>
      </header>
      {outcome.crisis_flagged ? (
        <CrisisAlert reasons={outcome.crisis_reasons} />
      ) : null}
      <div className="mt-3 space-y-3">
        <AnswersBlock title="Pre-call answers" answers={outcome.pre_answers} />
        {outcome.post_answers ? (
          <AnswersBlock title="Post-call answers" answers={outcome.post_answers} />
        ) : null}
        {outcome.counsellor_notes ? (
          <div>
            <p className="text-[11px] font-semibold tracking-wide text-fg/55">
              Counsellor notes
            </p>
            <p className="mt-1 whitespace-pre-wrap text-sm text-fg">
              {outcome.counsellor_notes}
            </p>
          </div>
        ) : null}
      </div>
    </DetailCard>
  )
}

export function AnswersBlock({
  title,
  answers,
}: {
  title: string
  answers: Record<string, string | number | string[] | null>
}) {
  return (
    <div>
      <p className="text-[11px] font-semibold tracking-wide text-fg/55">{title}</p>
      <pre className="mt-1 whitespace-pre-wrap wrap-break-word rounded-sm border border-fg/10 bg-bg px-2.5 py-2 text-xs text-fg/80">
        {JSON.stringify(answers, null, 2)}
      </pre>
    </div>
  )
}

export function CaseStatusPill({ status }: { status: CallbackCaseStatus }) {
  const tone =
    status === CallbackCaseStatus.CRISIS_ESCALATED
      ? "border-danger/30 bg-danger-soft text-danger-fg"
      : status === CallbackCaseStatus.COMPLETED
        ? "border-primary/30 bg-primary/10 text-primary"
        : status === CallbackCaseStatus.IN_PROGRESS
          ? "border-fg/25 bg-bg text-fg"
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
