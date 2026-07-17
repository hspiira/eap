import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  ClipboardList,
  ShieldCheck,
  XCircle,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { surveysApi } from "@/api/endpoints/surveys"
import { SURVEY_K_FLOOR } from "@/api/endpoints/surveys-fixture"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
  RailSection,
  Stat,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { WebhookSetupHelper } from "@/components/surveys/WebhookSetupHelper"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { nameInitials } from "@/lib/display"
import { defaultErrorMessage } from "@/lib/errors"
import { useEntityMutation } from "@/lib/queries"
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

  const closeMutation = useEntityMutation({
    resource: "surveys",
    mutationFn: () => surveysApi.close(surveyId),
    detailId: surveyId,
    onSuccess: () => {
      showSuccess("Survey closed")
    },
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  if (surveyQuery.isPending) {
    return (
      <PageShell icon={ClipboardList} breadcrumb="Insights · Surveys · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <DetailSkeleton />
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
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/surveys" })}
            aria-label="Back to surveys"
            title="Back to surveys"
            className="size-7 p-0 text-fg/70"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
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
          <Table className="w-full text-sm">
            <TableHeader className="bg-bg">
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
          Aggregate metrics are suppressed until at least {SURVEY_K_FLOOR} responses
          arrive. Free-text answers never appear in reports.
        </p>
      </RailSection>
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

