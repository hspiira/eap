import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ShieldCheck } from "lucide-react"

import { surveysApi } from "@/api/endpoints/surveys"
import { SURVEY_K_FLOOR } from "@/api/endpoints/surveys-fixture"
import { WebhookSetupHelper } from "@/components/surveys/WebhookSetupHelper"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { defaultErrorMessage } from "@/lib/errors"
import { SurveyStatus } from "@/types/enums"

export const Route = createFileRoute("/surveys/$surveyId")({
  component: SurveyDetailPage,
})

function SurveyDetailPage() {
  const { surveyId } = Route.useParams()
  const qc = useQueryClient()
  const { showSuccess, showError } = useToast()

  const surveyQuery = useQuery({
    queryKey: ["surveys", "detail", surveyId],
    queryFn: () => surveysApi.getById(surveyId),
  })
  const aggregateQuery = useQuery({
    queryKey: ["surveys", "aggregate", surveyId],
    queryFn: () => surveysApi.getAggregate(surveyId),
  })

  const rotateMutation = useMutation({
    mutationFn: () => surveysApi.rotateWebhookToken(surveyId),
    onSuccess: async () => {
      showSuccess("Webhook token rotated — update the survey provider")
      await qc.invalidateQueries({ queryKey: ["surveys", "detail", surveyId] })
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  const closeMutation = useMutation({
    mutationFn: () => surveysApi.close(surveyId),
    onSuccess: async () => {
      showSuccess("Survey closed")
      await qc.invalidateQueries({ queryKey: ["surveys"] })
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  if (surveyQuery.isPending) {
    return <p className="p-6 text-sm text-fg/60">Loading…</p>
  }
  if (!surveyQuery.data) {
    return <p className="p-6 text-sm text-fg/60">Survey not found.</p>
  }
  const survey = surveyQuery.data
  const aggregate = aggregateQuery.data
  const isClosed = survey.status === SurveyStatus.CLOSED

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-3xl space-y-5">
        <header>
          <Link to="/surveys" className="text-xs text-fg/60 hover:text-primary hover:underline">
            ← All surveys
          </Link>
          <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold text-fg">{survey.name}</h1>
              <p className="mt-1 text-sm text-fg/70">
                {new Date(survey.period_start).toLocaleDateString()} –{" "}
                {new Date(survey.period_end).toLocaleDateString()} · source: {survey.source} ·{" "}
                status:{" "}
                <span className="font-medium text-fg">{survey.status}</span> · responses:{" "}
                {survey.response_count}
              </p>
              {survey.description ? (
                <p className="mt-1 text-sm text-fg/70">{survey.description}</p>
              ) : null}
            </div>
            {!isClosed && (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={closeMutation.isPending}
                onClick={() => closeMutation.mutate()}
                className="rounded-none border-fg/30 text-fg"
              >
                {closeMutation.isPending ? "Closing…" : "Close survey"}
              </Button>
            )}
          </div>
        </header>

        <WebhookSetupHelper
          webhookUrl={survey.webhook_url}
          webhookToken={survey.webhook_token}
          onRotateToken={async () => {
            await rotateMutation.mutateAsync()
          }}
          rotating={rotateMutation.isPending}
          readOnly={isClosed}
        />

        <section className="border border-fg/20 bg-white p-4">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-fg">
            <ShieldCheck className="h-4 w-4 text-primary" /> Aggregated dashboard (no PII)
          </h2>
          {aggregateQuery.isPending ? (
            <p className="mt-2 text-sm text-fg/60">Computing…</p>
          ) : !aggregate ? (
            <p className="mt-2 text-sm text-fg/60">Aggregate unavailable.</p>
          ) : !aggregate.k_floor_met ? (
            <p className="mt-2 text-sm text-fg/70">
              <strong>Insufficient data.</strong> Aggregate metrics suppressed until at least{" "}
              {SURVEY_K_FLOOR} responses arrive (k-anon floor). Current: {aggregate.response_count}.
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              <p className="text-xs text-fg/60">
                {aggregate.response_count} responses
                {aggregate.satisfaction_mean !== null
                  ? ` · satisfaction mean: ${aggregate.satisfaction_mean}`
                  : ""}
                {aggregate.nps !== null ? ` · NPS: ${aggregate.nps}` : ""}
              </p>
              <table className="w-full border border-fg/10 text-sm">
                <thead className="bg-neutral-50 text-fg">
                  <tr>
                    <th className="border-b border-fg/10 px-2 py-1.5 text-left font-medium">
                      Question
                    </th>
                    <th className="border-b border-fg/10 px-2 py-1.5 text-right font-medium">
                      n
                    </th>
                    <th className="border-b border-fg/10 px-2 py-1.5 text-right font-medium">
                      Mean / Top
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {aggregate.question_summaries.map((s) => (
                    <tr key={s.question_key} className="text-fg/80">
                      <td className="border-b border-fg/10 px-2 py-1.5">{s.prompt}</td>
                      <td className="border-b border-fg/10 px-2 py-1.5 text-right">{s.n}</td>
                      <td className="border-b border-fg/10 px-2 py-1.5 text-right">
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
            </div>
          )}
        </section>
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
