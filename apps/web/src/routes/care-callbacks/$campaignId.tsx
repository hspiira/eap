import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowLeft,
  ChevronRight,
  FileBarChart,
  Phone,
  ShieldCheck,
} from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { K_ANON_FLOOR } from "@/api/endpoints/care-callbacks-fixture"
import { clientsApi } from "@/api/endpoints/clients"
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
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
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

export const Route = createFileRoute("/care-callbacks/$campaignId")({
  component: CampaignDetailPage,
})

type TabValue = "overview" | "cases" | "aggregate" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "cases", "aggregate", "history"]

function CampaignDetailPage() {
  const { campaignId } = Route.useParams()
  const navigate = useNavigate()
  const campaignQuery = useQuery({
    queryKey: ["care-callback-campaigns", "detail", campaignId],
    queryFn: () => careCallbacksApi.getCampaign(campaignId),
  })
  const casesQuery = useQuery({
    queryKey: ["care-callback-cases", "list", { campaign_id: campaignId }],
    queryFn: () => careCallbacksApi.listCases({ campaign_id: campaignId }),
  })
  const aggregateQuery = useQuery({
    queryKey: ["care-callback-campaigns", "aggregate", campaignId],
    queryFn: () => careCallbacksApi.getAggregate(campaignId),
  })

  const clientId = campaignQuery.data?.client_id
  const clientQuery = useQuery({
    queryKey: ["clients", "detail", clientId ?? ""],
    queryFn: () => clientsApi.getById(clientId as string),
    enabled: !!clientId,
  })

  if (campaignQuery.isPending) {
    return (
      <PageShell icon={Phone} breadcrumb="Care · Callback campaigns · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <DetailSkeleton />
        </div>
      </PageShell>
    )
  }
  if (!campaignQuery.data) {
    return (
      <PageShell icon={Phone} breadcrumb="Care · Callback campaigns · Not found">
        <EmptyState
          icon={Phone}
          title="Campaign not found"
          description="It may have been cancelled or never existed."
          action={
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => navigate({ to: "/care-callbacks" })}
            >
              <ArrowLeft className="size-4" />
              Back to campaigns
            </Button>
          }
        />
      </PageShell>
    )
  }

  const campaign = campaignQuery.data
  const cases = casesQuery.data?.items ?? []
  const aggregate = aggregateQuery.data ?? null
  const client = clientQuery.data ?? null

  return (
    <CampaignDetail
      campaign={campaign}
      cases={cases}
      aggregate={aggregate}
      client={client}
      casesLoading={casesQuery.isPending}
      aggregateLoading={aggregateQuery.isPending}
    />
  )
}

function CampaignDetail({
  campaign,
  cases,
  aggregate,
  client,
  casesLoading,
  aggregateLoading,
}: {
  campaign: CallbackCampaign
  cases: CallbackCase[]
  aggregate: CallbackCampaignAggregate | null
  client: Client | null
  casesLoading: boolean
  aggregateLoading: boolean
}) {
  const navigate = useNavigate()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")

  const total = campaign.case_count
  const completionPct = total
    ? Math.round((campaign.cases_completed / total) * 100)
    : 0
  const crisisCount = cases.filter((c) => c.crisis_flagged).length

  return (
    <PageShell
      icon={Phone}
      breadcrumb={`Care · Callback campaigns · ${campaign.name}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/care-callbacks" })}
            aria-label="Back to campaigns"
            title="Back to campaigns"
            className="size-7 p-0 text-fg/70"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
          <Link
            to="/reports/$templateSlug"
            params={{ templateSlug: "care-callback-summary" }}
            search={{ campaign_id: campaign.id }}
            className="inline-flex h-7 items-center gap-1.5 rounded-sm border border-fg/15 bg-bg px-2.5 text-sm font-medium text-fg hover:bg-surface-hover"
          >
            <FileBarChart className="size-3.5" />
            Wave summary
          </Link>
        </>
      }
    >
      <Hero campaign={campaign} client={client} />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="cases" count={cases.length}>
                  Cases
                </Tab>
                <Tab value="aggregate">Aggregate</Tab>
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Identity">
                    <DetailGrid>
                      <DetailRow label="Name" value={campaign.name} fullWidth />
                      <DetailRow
                        label="Description"
                        value={campaign.description}
                        fullWidth
                      />
                      <DetailRow
                        label="Status"
                        value={<CampaignStatusPill status={campaign.status} />}
                      />
                      <DetailRow
                        label="Sampling"
                        value={
                          <span className="font-mono">
                            {campaign.sampling}
                            {campaign.sample_size ? ` (n=${campaign.sample_size})` : ""}
                          </span>
                        }
                      />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Window">
                    <DetailGrid>
                      <DetailRow
                        label="Start"
                        value={new Date(campaign.period_start).toLocaleDateString()}
                      />
                      <DetailRow
                        label="End"
                        value={new Date(campaign.period_end).toLocaleDateString()}
                      />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Questionnaires">
                    <DetailGrid>
                      <DetailRow
                        label="Triage"
                        value={
                          <span className="font-mono">{campaign.questionnaire_code}</span>
                        }
                        fullWidth
                      />
                      <DetailRow
                        label="Follow-up"
                        value={
                          campaign.followup_questionnaire_code ? (
                            <span className="font-mono">
                              {campaign.followup_questionnaire_code}
                            </span>
                          ) : null
                        }
                        fullWidth
                      />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Counsellor pool">
                    {campaign.counsellor_user_ids.length === 0 ? (
                      <p className="text-xs text-fg/55">No counsellors assigned.</p>
                    ) : (
                      <ul className="space-y-1.5">
                        {campaign.counsellor_user_ids.map((id) => (
                          <li
                            key={id}
                            className="flex items-center gap-2 rounded-sm border border-fg/10 bg-bg px-2.5 py-1.5"
                          >
                            <span
                              aria-hidden
                              className="grid size-5 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                            >
                              U
                            </span>
                            <Link
                              to="/users/$userId"
                              params={{ userId: id }}
                              className="truncate font-mono text-xs text-fg hover:text-primary"
                            >
                              {id}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    )}
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="cases">
                <CasesPanel cases={cases} loading={casesLoading} />
              </TabPanel>

              <TabPanel value="aggregate">
                <AggregatePanel aggregate={aggregate} loading={aggregateLoading} />
              </TabPanel>

              <TabPanel value="history">
                <EmptyState
                  title="No activity yet"
                  description="Campaign lifecycle events will appear here once the audit feed is wired up."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              campaign={campaign}
              client={client}
              completionPct={completionPct}
              crisisCount={crisisCount}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({
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

function CasesPanel({
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

function AggregatePanel({
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

function topHistogramEntry(h: Record<string, number>): string {
  const entries = Object.entries(h)
  if (entries.length === 0) return "—"
  entries.sort((a, b) => b[1] - a[1])
  const [value, count] = entries[0]
  return `${value} (${count})`
}

function DetailRail({
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

function CaseStatusPill({ status }: { status: CallbackCaseStatus }) {
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

