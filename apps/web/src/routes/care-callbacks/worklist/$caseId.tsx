import { useMemo, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowLeft,
  Headphones,
  Phone,
  PlayCircle,
} from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { questionnairesApi } from "@/api/endpoints/questionnaires"
import { evaluateCrisisRules } from "@/api/endpoints/questionnaires-fixture"
import { CrisisAlert } from "@/components/care-callbacks/CrisisAlert"
import {
  type AnswersMap,
  QuestionnaireRenderer,
} from "@/components/care-callbacks/QuestionnaireRenderer"
import {
  DetailCard,
  RailSection,
  Stat,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { nameInitials } from "@/lib/display"
import { defaultErrorMessage } from "@/lib/errors"
import { useEntityMutation } from "@/lib/queries"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/slices/authSlice"
import type { CallbackCase, CallbackOutcome } from "@/types/entities"
import { CallbackCaseStatus } from "@/types/enums"

export const Route = createFileRoute("/care-callbacks/worklist/$caseId")({
  component: CaseTriagePage,
})

type TabValue = "triage" | "outcome" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["triage", "outcome", "history"]

function CaseTriagePage() {
  const { caseId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const userId = useAuthStore((s) => s.user_id) ?? "user-helen"

  const caseQuery = useQuery({
    queryKey: ["care-callback-cases", "detail", caseId],
    queryFn: () => careCallbacksApi.getCase(caseId),
  })
  const outcomeQuery = useQuery({
    queryKey: ["care-callback-cases", "outcome", caseId],
    queryFn: () => careCallbacksApi.getOutcomeForCase(caseId),
  })

  const campaignId = caseQuery.data?.campaign_id
  const campaignQuery = useQuery({
    queryKey: ["care-callback-campaigns", "detail", campaignId ?? ""],
    queryFn: () => careCallbacksApi.getCampaign(campaignId as string),
    enabled: !!campaignId,
  })
  const campaign = campaignQuery.data

  const triageCode = campaign?.questionnaire_code ?? null
  const triageQuery = useQuery({
    queryKey: ["questionnaires", "by-code", triageCode ?? ""],
    queryFn: () => questionnairesApi.getByCode(triageCode as string),
    enabled: !!triageCode,
    staleTime: 60_000,
  })
  const triage = triageQuery.data

  const followupCode = campaign?.followup_questionnaire_code ?? null
  const followupQuery = useQuery({
    queryKey: ["questionnaires", "by-code", followupCode ?? ""],
    queryFn: () => questionnairesApi.getByCode(followupCode as string),
    enabled: !!followupCode,
    staleTime: 60_000,
  })
  const followup = followupQuery.data

  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "triage")
  const [preAnswers, setPreAnswers] = useState<AnswersMap>({})
  const [postAnswers, setPostAnswers] = useState<AnswersMap>({})
  const [counsellorNotes, setCounsellorNotes] = useState("")
  const [finalStatus, setFinalStatus] = useState<CallbackCaseStatus>(
    CallbackCaseStatus.COMPLETED,
  )

  const crisisReasons = useMemo(() => evaluateCrisisRules(preAnswers), [preAnswers])
  const crisisActive = crisisReasons.length > 0

  const startMutation = useEntityMutation({
    resource: "care-callback-cases",
    mutationFn: () => careCallbacksApi.startCase(caseId),
    detailId: caseId,
    invalidateKeys: campaignId
      ? [["care-callback-campaigns", "detail", campaignId]]
      : [],
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  const submitMutation = useEntityMutation({
    resource: "care-callback-cases",
    mutationFn: () =>
      careCallbacksApi.submitOutcome({
        case_id: caseId,
        questionnaire_code: campaign!.questionnaire_code,
        followup_questionnaire_code: campaign!.followup_questionnaire_code ?? null,
        pre_answers: preAnswers,
        post_answers: followup && hasAnyAnswer(postAnswers) ? postAnswers : null,
        counsellor_notes: counsellorNotes.trim() || null,
        final_status: finalStatus,
        recorded_by_user_id: userId,
      }),
    detailId: caseId,
    invalidateKeys: campaignId
      ? [
          ["care-callback-campaigns", "detail", campaignId],
          ["care-callback-campaigns", "aggregate", campaignId],
        ]
      : [],
    onSuccess: (outcome) => {
      showSuccess(
        outcome.crisis_flagged ? "Outcome saved · crisis escalated" : "Outcome saved",
      )
      navigate({ to: "/care-callbacks/worklist" })
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  if (caseQuery.isPending) {
    return (
      <PageShell icon={Headphones} breadcrumb="Care · My worklist · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <DetailSkeleton mainPanels={2} />
        </div>
      </PageShell>
    )
  }
  if (!caseQuery.data) {
    return (
      <PageShell icon={Headphones} breadcrumb="Care · My worklist · Not found">
        <EmptyState
          icon={Headphones}
          title="Case not found"
          description="It may have been reassigned or closed."
          action={
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => navigate({ to: "/care-callbacks/worklist" })}
            >
              <ArrowLeft className="size-4" />
              Back to worklist
            </Button>
          }
        />
      </PageShell>
    )
  }

  const callCase = caseQuery.data
  const existingOutcome = outcomeQuery.data ?? null
  const isClosed =
    callCase.status === CallbackCaseStatus.COMPLETED ||
    callCase.status === CallbackCaseStatus.CRISIS_ESCALATED ||
    callCase.status === CallbackCaseStatus.DECLINED
  const canStart = !isClosed && callCase.status === CallbackCaseStatus.QUEUED
  const canSubmit = !isClosed && triage && requiredAnswered(triage, preAnswers)

  return (
    <PageShell
      icon={Headphones}
      breadcrumb={`Care · My worklist · ${callCase.person_display_name}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/care-callbacks/worklist" })}
            aria-label="Back to worklist"
            title="Back to worklist"
            className="size-7 p-0 text-fg/70"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
          {canStart ? (
            <>
              <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
              <Button
                size="sm"
                className="h-7 gap-1.5 px-2.5"
                disabled={startMutation.isPending}
                onClick={() => startMutation.mutate()}
              >
                <PlayCircle className="size-3.5" />
                {startMutation.isPending ? "Opening…" : "Open case"}
              </Button>
            </>
          ) : null}
        </>
      }
    >
      <Hero callCase={callCase} campaignName={campaign?.name ?? null} />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            {existingOutcome ? (
              <ExistingOutcomeCard outcome={existingOutcome} />
            ) : (
              <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
                <TabsList className="-mx-3 mb-4 px-3">
                  <Tab value="triage">Triage</Tab>
                  <Tab value="outcome">Outcome</Tab>
                  <Tab value="history">History</Tab>
                </TabsList>

                <TabPanel value="triage">
                  {!triage ? (
                    <p className="text-sm text-fg/65">Loading triage form…</p>
                  ) : (
                    <div className="space-y-4">
                      <DetailCard title={triage.title}>
                        <QuestionnaireRenderer
                          questionnaire={triage}
                          answers={preAnswers}
                          onChange={(key, v) =>
                            setPreAnswers((prev) => {
                              const next = { ...prev }
                              if (v === null) delete next[key]
                              else next[key] = v
                              return next
                            })
                          }
                          readOnly={isClosed}
                        />
                      </DetailCard>
                      {crisisActive ? <CrisisAlert reasons={crisisReasons} /> : null}
                      {followup ? (
                        <DetailCard title={`Post-call · ${followup.title}`}>
                          <QuestionnaireRenderer
                            questionnaire={followup}
                            answers={postAnswers}
                            onChange={(key, v) =>
                              setPostAnswers((prev) => {
                                const next = { ...prev }
                                if (v === null) delete next[key]
                                else next[key] = v
                                return next
                              })
                            }
                            readOnly={isClosed}
                          />
                        </DetailCard>
                      ) : null}
                    </div>
                  )}
                </TabPanel>

                <TabPanel value="outcome">
                  <DetailCard title="Outcome">
                    <FormSection
                      title="Counsellor notes"
                      description="Internal — never surfaced in aggregate reports."
                    >
                      <FormField label="Notes" optional htmlFor="cc-notes">
                        <Textarea
                          id="cc-notes"
                          rows={4}
                          disabled={isClosed}
                          value={counsellorNotes}
                          onChange={(e) => setCounsellorNotes(e.target.value)}
                        />
                      </FormField>
                    </FormSection>
                    <FormSection title="Final status">
                      <FormField
                        label="Outcome status"
                        required
                        description={
                          crisisActive
                            ? "Crisis flag latches the case to Crisis Escalated on submit."
                            : "Choose how this attempt closed."
                        }
                        htmlFor="cc-status"
                      >
                        <Select
                          disabled={isClosed || crisisActive}
                          value={finalStatus}
                          onValueChange={(v) => setFinalStatus(v as CallbackCaseStatus)}
                        >
                          <SelectTrigger id="cc-status">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value={CallbackCaseStatus.COMPLETED}>Completed</SelectItem>
                            <SelectItem value={CallbackCaseStatus.NO_ANSWER}>No answer</SelectItem>
                            <SelectItem value={CallbackCaseStatus.DECLINED}>Declined</SelectItem>
                          </SelectContent>
                        </Select>
                      </FormField>
                    </FormSection>
                    <div className="flex justify-end gap-2 border-t border-fg/10 pt-4">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => navigate({ to: "/care-callbacks/worklist" })}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        disabled={!canSubmit || submitMutation.isPending}
                        onClick={() => submitMutation.mutate()}
                      >
                        {submitMutation.isPending ? "Saving…" : "Save outcome"}
                      </Button>
                    </div>
                  </DetailCard>
                </TabPanel>

                <TabPanel value="history">
                  <EmptyState
                    title="No activity yet"
                    description="Lifecycle events will appear here once the audit feed is wired up."
                  />
                </TabPanel>
              </Tabs>
            )}
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              callCase={callCase}
              campaignId={campaign?.id ?? callCase.campaign_id}
              campaignName={campaign?.name ?? null}
              crisisActive={crisisActive || callCase.crisis_flagged}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({
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

function DetailRail({
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

function ExistingOutcomeCard({ outcome }: { outcome: CallbackOutcome }) {
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

function AnswersBlock({
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

function CaseStatusPill({ status }: { status: CallbackCaseStatus }) {
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

function hasAnyAnswer(map: AnswersMap): boolean {
  return Object.values(map).some(
    (v) => v !== null && v !== undefined && !(Array.isArray(v) && v.length === 0),
  )
}

function requiredAnswered(
  questionnaire: { questions: Array<{ key: string; required: boolean }> },
  answers: AnswersMap,
): boolean {
  return questionnaire.questions.every((q) => {
    if (!q.required) return true
    const v = answers[q.key]
    if (v === null || v === undefined) return false
    if (Array.isArray(v) && v.length === 0) return false
    if (typeof v === "string" && v.trim() === "") return false
    return true
  })
}
