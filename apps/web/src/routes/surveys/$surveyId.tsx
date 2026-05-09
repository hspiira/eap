import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  ClipboardList,
  RotateCw,
  ShieldCheck,
  XCircle,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { surveysApi } from "@/api/endpoints/surveys"
import { SURVEY_K_FLOOR } from "@/api/endpoints/surveys-fixture"
import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { WebhookSetupHelper } from "@/components/surveys/WebhookSetupHelper"
import { SurveyDetailSkeleton } from "@/components/SurveysPageSkeletons"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { defaultErrorMessage } from "@/lib/errors"
import { cn } from "@/lib/utils"
import { SurveyStatusPill } from "@/routes/surveys/index"
import type { Client, Survey, SurveyAggregate } from "@/types/entities"
import { SurveyStatus } from "@/types/enums"

export const Route = createFileRoute("/surveys/$surveyId")({
  component: SurveyDetailPage,
})

type TabValue = "overview" | "webhook" | "aggregate" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = [
  "overview",
  "webhook",
  "aggregate",
  "history",
]

function SurveyDetailPage() {
  const { surveyId } = Route.useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { showSuccess, showError } = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")

  const surveyQuery = useQuery({
    queryKey: ["surveys", "detail", surveyId],
    queryFn: () => surveysApi.getById(surveyId),
  })
  const aggregateQuery = useQuery({
    queryKey: ["surveys", "aggregate", surveyId],
    queryFn: () => surveysApi.getAggregate(surveyId),
  })
  const clientId = surveyQuery.data?.client_id
  const clientQuery = useQuery({
    queryKey: ["clients", "detail", clientId ?? ""],
    queryFn: () => clientsApi.getById(clientId as string),
    enabled: !!clientId,
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
    return (
      <PageShell icon={ClipboardList} breadcrumb="Insights · Surveys · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <SurveyDetailSkeleton />
        </div>
      </PageShell>
    )
  }
  if (!surveyQuery.data) {
    return (
      <PageShell icon={ClipboardList} breadcrumb="Insights · Surveys · Not found">
        <EmptyState
          icon={ClipboardList}
          title="Survey not found"
          description="It may have been closed or never existed."
          action={
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => navigate({ to: "/surveys" })}
            >
              <ArrowLeft className="size-4" />
              Back to surveys
            </Button>
          }
        />
      </PageShell>
    )
  }

  const survey = surveyQuery.data
  const aggregate = aggregateQuery.data ?? null
  const client = clientQuery.data ?? null
  const isClosed = survey.status === SurveyStatus.CLOSED

  return (
    <PageShell
      icon={ClipboardList}
      breadcrumb={`Insights · Surveys · ${survey.name}`}
      actions={
        <>
          <button
            type="button"
            onClick={() => navigate({ to: "/surveys" })}
            aria-label="Back to surveys"
            title="Back to surveys"
            className="grid size-7 place-items-center rounded-sm text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
          >
            <ArrowLeft className="size-3.5" />
          </button>
          <button
            type="button"
            onClick={() => {
              surveyQuery.refetch()
              aggregateQuery.refetch()
            }}
            aria-label="Refresh"
            title="Refresh"
            className="grid size-7 place-items-center rounded-sm text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
          >
            <RotateCw className="size-3.5" />
          </button>
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          {!isClosed ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 gap-1.5 px-2.5"
              disabled={closeMutation.isPending}
              onClick={() => closeMutation.mutate()}
            >
              <XCircle className="size-3.5" />
              {closeMutation.isPending ? "Closing…" : "Close survey"}
            </Button>
          ) : null}
        </>
      }
    >
      <Hero survey={survey} client={client} />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="webhook">Webhook</Tab>
                <Tab value="aggregate">Aggregate</Tab>
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Identity">
                    <DetailGrid>
                      <DetailRow label="Name" value={survey.name} fullWidth />
                      <DetailRow
                        label="Description"
                        value={survey.description}
                        fullWidth
                      />
                      <DetailRow
                        label="Status"
                        value={<SurveyStatusPill status={survey.status} />}
                      />
                      <DetailRow label="Source" value={survey.source} />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Window">
                    <DetailGrid>
                      <DetailRow
                        label="Start"
                        value={new Date(survey.period_start).toLocaleDateString()}
                      />
                      <DetailRow
                        label="End"
                        value={new Date(survey.period_end).toLocaleDateString()}
                      />
                      <DetailRow
                        label="First response"
                        value={
                          survey.first_response_at
                            ? new Date(survey.first_response_at).toLocaleString()
                            : null
                        }
                      />
                      <DetailRow
                        label="Closed"
                        value={
                          survey.closed_at
                            ? new Date(survey.closed_at).toLocaleString()
                            : null
                        }
                      />
                    </DetailGrid>
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="webhook">
                <WebhookSetupHelper
                  webhookUrl={survey.webhook_url}
                  webhookToken={survey.webhook_token}
                  onRotateToken={async () => {
                    await rotateMutation.mutateAsync()
                  }}
                  rotating={rotateMutation.isPending}
                  readOnly={isClosed}
                />
              </TabPanel>

              <TabPanel value="aggregate">
                <AggregatePanel
                  aggregate={aggregate}
                  loading={aggregateQuery.isPending}
                />
              </TabPanel>

              <TabPanel value="history">
                <EmptyState
                  title="No activity yet"
                  description="Webhook deliveries and lifecycle events will appear here once the audit feed is wired up."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              survey={survey}
              client={client}
              aggregate={aggregate}
              onOpenWaveSummary={() =>
                navigate({
                  to: "/reports/$templateSlug",
                  params: { templateSlug: "care-callback-summary" },
                })
              }
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({ survey, client }: { survey: Survey; client: Client | null }) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <ClipboardList className="size-4" />
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {survey.name}
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
      <SurveyStatusPill status={survey.status} />
      <span className="font-mono text-xs text-fg/55">{survey.source}</span>
    </div>
  )
}

function AggregatePanel({
  aggregate,
  loading,
}: {
  aggregate: SurveyAggregate | null
  loading: boolean
}) {
  if (loading) return <p className="text-sm text-fg/65">Computing aggregate…</p>
  if (!aggregate) {
    return (
      <EmptyState
        title="Aggregate unavailable"
        description="Try again once at least one response is in."
      />
    )
  }
  if (!aggregate.k_floor_met) {
    return (
      <DetailCard title="Aggregated dashboard (no PII)">
        <div className="flex items-start gap-2.5">
          <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
          <div className="min-w-0 flex-1 text-sm">
            <p className="font-medium text-fg">Insufficient data</p>
            <p className="mt-0.5 text-fg/60">
              Aggregate metrics suppressed until at least {SURVEY_K_FLOOR} responses arrive
              (k-anon floor). Currently {aggregate.response_count}.
            </p>
          </div>
        </div>
      </DetailCard>
    )
  }
  return (
    <div className="space-y-4">
      <DetailCard title="Headline counts">
        <DetailGrid>
          <DetailRow label="Responses" value={aggregate.response_count} />
          {aggregate.satisfaction_mean != null ? (
            <DetailRow
              label="Satisfaction (mean)"
              value={aggregate.satisfaction_mean.toFixed(2)}
            />
          ) : null}
          {aggregate.nps != null ? (
            <DetailRow label="NPS" value={aggregate.nps} />
          ) : null}
        </DetailGrid>
      </DetailCard>
      <DetailCard title="Per-question outcomes">
        <div className="overflow-hidden rounded-sm border border-fg/10">
          <table className="w-full text-sm">
            <thead className="bg-bg">
              <tr className="text-left text-[11px] font-semibold uppercase tracking-wide text-fg/55">
                <th className="border-b border-fg/15 px-3 py-2">Question</th>
                <th className="w-16 border-b border-fg/15 px-3 py-2 text-right">n</th>
                <th className="w-32 border-b border-fg/15 px-3 py-2 text-right">
                  Mean / Top
                </th>
              </tr>
            </thead>
            <tbody>
              {aggregate.question_summaries.map((s) => (
                <tr key={s.question_key} className="border-b border-fg/10 last:border-0">
                  <td className="px-3 py-2 text-fg">{s.prompt}</td>
                  <td className="px-3 py-2 text-right font-mono text-fg">{s.n}</td>
                  <td className="px-3 py-2 text-right font-mono text-fg/80">
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
      </DetailCard>
    </div>
  )
}

function DetailRail({
  survey,
  client,
  aggregate,
}: {
  survey: Survey
  client: Client | null
  aggregate: SurveyAggregate | null
  onOpenWaveSummary: () => void
}) {
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Responses" value={survey.response_count} />
          <Stat
            label="Satisfaction"
            value={
              aggregate?.satisfaction_mean != null
                ? aggregate.satisfaction_mean.toFixed(2)
                : "—"
            }
          />
          <Stat
            label="NPS"
            value={aggregate?.nps != null ? String(aggregate.nps) : "—"}
          />
          <Stat
            label="K-floor"
            value={aggregate?.k_floor_met ? "Met" : `${SURVEY_K_FLOOR}+`}
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
              {clientInitial(client.name)}
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
          Aggregate metrics are suppressed until at least {SURVEY_K_FLOOR} responses
          arrive. Free-text answers never appear in reports.
        </p>
      </RailSection>
    </div>
  )
}

function DetailCard({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-sm border border-fg/10 bg-surface p-4">
      <h3 className="mb-3 text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      {children}
    </section>
  )
}

function RailSection({
  title,
  children,
  className,
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={cn("space-y-2", className)}>
      <h3 className="text-xs font-semibold tracking-wide text-fg/55">{title}</h3>
      {children}
    </section>
  )
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-sm border border-fg/10 bg-surface px-3 py-2">
      <div className="text-[11px] font-medium tracking-wide text-fg/55">{label}</div>
      <div className="mt-0.5 font-mono text-base font-semibold text-fg">{value}</div>
    </div>
  )
}

function DetailGrid({ children }: { children: React.ReactNode }) {
  return <dl className="grid grid-cols-2 gap-x-3 gap-y-2.5">{children}</dl>
}

function DetailRow({
  label,
  value,
  fullWidth,
}: {
  label: string
  value: React.ReactNode
  fullWidth?: boolean
}) {
  return (
    <div className={cn(fullWidth && "col-span-2")}>
      <dt className="text-[11px] font-medium tracking-wide text-fg/55">{label}</dt>
      <dd className="mt-0.5 truncate text-sm text-fg">
        {value || <span className="text-fg/40">—</span>}
      </dd>
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

function clientInitial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
}
