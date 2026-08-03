import { useMemo, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  Headphones,
  PlayCircle,
} from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { questionnairesApi } from "@/api/endpoints/questionnaires"
import { evaluateCrisisRules } from "@/api/endpoints/questionnaires-fixture"
import {
  DetailRail,
  ExistingOutcomeCard,
  Hero,
} from "@/components/care-callbacks/CaseTriageWidgets"
import { CrisisAlert } from "@/components/care-callbacks/CrisisAlert"
import {
  type AnswersMap,
  QuestionnaireRenderer,
} from "@/components/care-callbacks/QuestionnaireRenderer"
import {
  DetailCard,
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
import { defaultErrorMessage } from "@/lib/errors"
import { useEntityMutation } from "@/lib/queries"
import { useAuthStore } from "@/store/slices/authSlice"
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
