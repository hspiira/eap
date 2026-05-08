import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { useMemo, useState } from "react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { evaluateCrisisRules } from "@/api/endpoints/questionnaires-fixture"
import { questionnairesApi } from "@/api/endpoints/questionnaires"
import { CrisisAlert } from "@/components/care-callbacks/CrisisAlert"
import {
  type AnswersMap,
  QuestionnaireRenderer,
} from "@/components/care-callbacks/QuestionnaireRenderer"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { defaultErrorMessage } from "@/lib/errors"
import { useAuthStore } from "@/store/slices/authSlice"
import { CallbackCaseStatus } from "@/types/enums"

export const Route = createFileRoute("/care-callbacks/worklist/$caseId")({
  component: CaseTriagePage,
})

function CaseTriagePage() {
  const { caseId } = Route.useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
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

  const [preAnswers, setPreAnswers] = useState<AnswersMap>({})
  const [postAnswers, setPostAnswers] = useState<AnswersMap>({})
  const [counsellorNotes, setCounsellorNotes] = useState("")
  const [finalStatus, setFinalStatus] = useState<CallbackCaseStatus>(CallbackCaseStatus.COMPLETED)

  const crisisReasons = useMemo(() => evaluateCrisisRules(preAnswers), [preAnswers])
  const crisisActive = crisisReasons.length > 0

  const startMutation = useMutation({
    mutationFn: () => careCallbacksApi.startCase(caseId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["care-callback-cases"] })
      await qc.invalidateQueries({
        queryKey: ["care-callback-campaigns", "detail", campaignId],
      })
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  const submitMutation = useMutation({
    mutationFn: () =>
      careCallbacksApi.submitOutcome({
        case_id: caseId,
        questionnaire_code: campaign!.questionnaire_code,
        followup_questionnaire_code: campaign!.followup_questionnaire_code ?? null,
        pre_answers: preAnswers,
        post_answers:
          followup && hasAnyAnswer(postAnswers) ? postAnswers : null,
        counsellor_notes: counsellorNotes.trim() || null,
        final_status: finalStatus,
        recorded_by_user_id: userId,
      }),
    onSuccess: async (outcome) => {
      showSuccess(outcome.crisis_flagged ? "Outcome saved · crisis escalated" : "Outcome saved")
      await qc.invalidateQueries({ queryKey: ["care-callback-cases"] })
      await qc.invalidateQueries({
        queryKey: ["care-callback-campaigns", "detail", campaignId],
      })
      await qc.invalidateQueries({
        queryKey: ["care-callback-campaigns", "aggregate", campaignId],
      })
      navigate({ to: "/care-callbacks/worklist" })
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  if (caseQuery.isPending) {
    return <p className="p-6 text-sm text-ink/60">Loading case…</p>
  }
  if (!caseQuery.data) {
    return <p className="p-6 text-sm text-ink/60">Case not found.</p>
  }
  const callCase = caseQuery.data
  const existingOutcome = outcomeQuery.data

  const isClosed =
    callCase.status === CallbackCaseStatus.COMPLETED ||
    callCase.status === CallbackCaseStatus.CRISIS_ESCALATED ||
    callCase.status === CallbackCaseStatus.DECLINED
  const canStart = !isClosed && callCase.status === CallbackCaseStatus.QUEUED
  const canSubmit = !isClosed && triage && requiredAnswered(triage, preAnswers)

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-3xl space-y-5">
        <header>
          <Link
            to="/care-callbacks/worklist"
            className="text-xs text-ink/60 hover:text-natural hover:underline"
          >
            ← My worklist
          </Link>
          <h1 className="mt-2 text-xl font-semibold text-ink">{callCase.person_display_name}</h1>
          <p className="mt-1 text-sm text-ink/70">
            Campaign: {campaign?.name ?? callCase.campaign_id} · status:{" "}
            <span className="font-medium text-ink">{callCase.status}</span> · attempts:{" "}
            {callCase.attempt_count}
          </p>
        </header>

        {existingOutcome ? (
          <ExistingOutcomeCard outcome={existingOutcome} />
        ) : (
          <>
            {canStart && (
              <Button
                type="button"
                disabled={startMutation.isPending}
                onClick={() => startMutation.mutate()}
                className="rounded-none bg-natural text-white hover:bg-natural-dark"
              >
                {startMutation.isPending ? "Opening…" : "Open case"}
              </Button>
            )}

            {!triage ? (
              <p className="text-sm text-ink/60">Loading triage form…</p>
            ) : (
              <>
                <section className="border border-ink/20 bg-white p-4 space-y-4">
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
                </section>

                {crisisActive && <CrisisAlert reasons={crisisReasons} />}

                {followup && (
                  <section className="border border-ink/20 bg-white p-4 space-y-4">
                    <p className="text-xs uppercase tracking-wide text-ink/60">Post-call</p>
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
                  </section>
                )}

                <section className="border border-ink/20 bg-white p-4 space-y-2">
                  <label
                    htmlFor="notes"
                    className="block text-sm font-medium text-ink"
                  >
                    Counsellor notes (not surfaced in aggregate report)
                  </label>
                  <textarea
                    id="notes"
                    rows={3}
                    disabled={isClosed}
                    value={counsellorNotes}
                    onChange={(e) => setCounsellorNotes(e.target.value)}
                    className="flex w-full border border-ink/30 bg-white px-3 py-2 text-sm text-ink rounded-none"
                  />
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <label
                        htmlFor="final_status"
                        className="block text-sm font-medium text-ink"
                      >
                        Outcome status
                      </label>
                      <select
                        id="final_status"
                        disabled={isClosed || crisisActive}
                        value={finalStatus}
                        onChange={(e) =>
                          setFinalStatus(e.target.value as CallbackCaseStatus)
                        }
                        className="mt-1 flex h-9 w-full border border-ink/30 bg-white px-3 py-2 rounded-none text-ink"
                      >
                        <option value={CallbackCaseStatus.COMPLETED}>Completed</option>
                        <option value={CallbackCaseStatus.NO_ANSWER}>No answer</option>
                        <option value={CallbackCaseStatus.DECLINED}>Declined</option>
                      </select>
                      {crisisActive && (
                        <p className="mt-1 text-xs text-danger-soft">
                          Crisis flag latches the case to <em>Crisis Escalated</em> on submit.
                        </p>
                      )}
                    </div>
                  </div>
                </section>

                <div className="flex gap-2">
                  <Button
                    type="button"
                    disabled={!canSubmit || submitMutation.isPending}
                    onClick={() => submitMutation.mutate()}
                    className="rounded-none bg-natural text-white hover:bg-natural-dark"
                  >
                    {submitMutation.isPending ? "Saving…" : "Save outcome"}
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    className="rounded-none border-ink/30 text-ink"
                    onClick={() => navigate({ to: "/care-callbacks/worklist" })}
                  >
                    Cancel
                  </Button>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function hasAnyAnswer(map: AnswersMap): boolean {
  return Object.values(map).some((v) => v !== null && v !== undefined && !(Array.isArray(v) && v.length === 0))
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

function ExistingOutcomeCard({ outcome }: { outcome: NonNullable<Awaited<ReturnType<typeof careCallbacksApi.getOutcomeForCase>>> }) {
  return (
    <section className="border border-ink/20 bg-white p-4 space-y-3">
      <header className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">Outcome on file</h2>
        <span className="text-xs text-ink/60">
          {new Date(outcome.recorded_at).toLocaleString()} · by {outcome.recorded_by_user_id}
        </span>
      </header>
      {outcome.crisis_flagged && <CrisisAlert reasons={outcome.crisis_reasons} />}
      <div>
        <p className="text-xs uppercase tracking-wide text-ink/60">Pre-call answers</p>
        <pre className="mt-1 whitespace-pre-wrap wrap-break-word border border-ink/10 bg-neutral-50 p-2 text-xs text-ink/80">
          {JSON.stringify(outcome.pre_answers, null, 2)}
        </pre>
      </div>
      {outcome.post_answers ? (
        <div>
          <p className="text-xs uppercase tracking-wide text-ink/60">Post-call answers</p>
          <pre className="mt-1 whitespace-pre-wrap wrap-break-word border border-ink/10 bg-neutral-50 p-2 text-xs text-ink/80">
            {JSON.stringify(outcome.post_answers, null, 2)}
          </pre>
        </div>
      ) : null}
      {outcome.counsellor_notes ? (
        <div>
          <p className="text-xs uppercase tracking-wide text-ink/60">Counsellor notes</p>
          <p className="mt-1 text-sm text-ink/80 whitespace-pre-wrap">{outcome.counsellor_notes}</p>
        </div>
      ) : null}
    </section>
  )
}

