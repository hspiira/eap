import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  FileBarChart,
  Phone,
} from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { clientsApi } from "@/api/endpoints/clients"
import {
  AggregatePanel,
  CasesPanel,
  DetailRail,
  Hero,
} from "@/components/care-callbacks/CampaignDetailWidgets"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { Button } from "@/components/ui/button"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { CampaignStatusPill } from "@/routes/care-callbacks/index"
import type {
  CallbackCampaign,
  CallbackCampaignAggregate,
  CallbackCase,
  Client,
} from "@/types/entities"

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

