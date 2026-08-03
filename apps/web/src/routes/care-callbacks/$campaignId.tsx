import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
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
  CounsellorPoolDialog,
  DetailRail,
  EnrolDialog,
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
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey } from "@/lib/queries"
import { CampaignStatusPill } from "@/routes/care-callbacks/index"
import type {
  CallbackCampaign,
  CallbackCampaignAggregate,
  Client,
  OutreachRecord,
} from "@/types/entities"
import { CareCallbackCampaignStatus, OutreachStatus } from "@/types/enums"

export const Route = createFileRoute("/care-callbacks/$campaignId")({
  component: CampaignDetailPage,
})

type TabValue = "overview" | "cases" | "aggregate" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "cases", "aggregate", "history"]

function CampaignDetailPage() {
  const { campaignId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccess, showError } = useToast()
  const [actionLoading, setActionLoading] = useState(false)
  const [poolOpen, setPoolOpen] = useState(false)
  const [enrolOpen, setEnrolOpen] = useState(false)

  const campaignQuery = useQuery({
    queryKey: ["care-callback-campaigns", "detail", campaignId],
    queryFn: () => careCallbacksApi.getCampaign(campaignId),
  })
  const casesQuery = useQuery({
    queryKey: ["outreach-records", "for-campaign", campaignId],
    queryFn: () => careCallbacksApi.listOutreachForCampaign(campaignId, { limit: 200 }),
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

  const refreshCampaign = () =>
    queryClient.invalidateQueries({ queryKey: entityDetailKey("care-callback-campaigns", campaignId) })
  const refreshCases = () =>
    queryClient.invalidateQueries({ queryKey: ["outreach-records", "for-campaign", campaignId] })

  const runAction = async (action: () => Promise<unknown>, successMessage: string) => {
    setActionLoading(true)
    try {
      await action()
      await refreshCampaign()
      showSuccess(successMessage)
    } catch (err) {
      showError(normalizeErrorMessage(err, "Action failed — please try again"))
    } finally {
      setActionLoading(false)
    }
  }

  const handleActivate = () =>
    runAction(() => careCallbacksApi.activateCampaign(campaignId), "Campaign activated")
  const handleComplete = () =>
    runAction(() => careCallbacksApi.completeCampaign(campaignId), "Campaign completed")
  const handleArchive = () =>
    runAction(() => careCallbacksApi.archiveCampaign(campaignId), "Campaign archived")

  const handleSavePool = async (pool: string[]) => {
    try {
      await careCallbacksApi.updateCounsellorPool(campaignId, pool)
      await refreshCampaign()
      showSuccess("Counsellor pool updated")
    } catch (err) {
      showError(normalizeErrorMessage(err, "Could not update counsellor pool"))
      throw err
    }
  }

  const handleEnrol = async (personIds: string[]) => {
    try {
      await careCallbacksApi.enrol(campaignId, personIds)
      await refreshCases()
      showSuccess(`Enrolled ${personIds.length} ${personIds.length === 1 ? "person" : "persons"}`)
    } catch (err) {
      showError(normalizeErrorMessage(err, "Could not enrol persons"))
      throw err
    }
  }

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
          description="It may have been archived or never existed."
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
    <>
      <CampaignDetail
        campaign={campaign}
        cases={cases}
        aggregate={aggregate}
        client={client}
        casesLoading={casesQuery.isPending}
        aggregateLoading={aggregateQuery.isPending}
        actionLoading={actionLoading}
        onActivate={handleActivate}
        onComplete={handleComplete}
        onArchive={handleArchive}
        onEditPool={() => setPoolOpen(true)}
        onEnrol={() => setEnrolOpen(true)}
      />
      <CounsellorPoolDialog
        open={poolOpen}
        onOpenChange={setPoolOpen}
        currentPool={campaign.counsellor_pool}
        onSave={handleSavePool}
      />
      <EnrolDialog open={enrolOpen} onOpenChange={setEnrolOpen} onEnrol={handleEnrol} />
    </>
  )
}

function CampaignDetail({
  campaign,
  cases,
  aggregate,
  client,
  casesLoading,
  aggregateLoading,
  actionLoading,
  onActivate,
  onComplete,
  onArchive,
  onEditPool,
  onEnrol,
}: {
  campaign: CallbackCampaign
  cases: OutreachRecord[]
  aggregate: CallbackCampaignAggregate | null
  client: Client | null
  casesLoading: boolean
  aggregateLoading: boolean
  actionLoading: boolean
  onActivate: () => void
  onComplete: () => void
  onArchive: () => void
  onEditPool: () => void
  onEnrol: () => void
}) {
  const navigate = useNavigate()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")

  const total = campaign.target_count
  // completed_count is a known BE gap (nothing calls increment_completed()) —
  // derive from the fetched records instead of trusting the campaign field.
  const completedCount = cases.filter((c) => c.status === OutreachStatus.COMPLETED).length
  const completionPct = total ? Math.round((completedCount / total) * 100) : 0
  const inProgressCount = cases.filter(
    (c) => c.status === OutreachStatus.ASSIGNED || c.status === OutreachStatus.CONTACTED,
  ).length
  const crisisCount = cases.filter((c) => c.crisis_flag).length

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
                        label="Sampling notes"
                        value={campaign.sampling_notes}
                        fullWidth
                      />
                      <DetailRow
                        label="Status"
                        value={<CampaignStatusPill status={campaign.status} />}
                      />
                      <DetailRow label="Target" value={campaign.target_count} />
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
                      <DetailRow
                        label="Activated"
                        value={
                          campaign.activated_at
                            ? new Date(campaign.activated_at).toLocaleDateString()
                            : null
                        }
                      />
                      <DetailRow
                        label="Completed"
                        value={
                          campaign.completed_at
                            ? new Date(campaign.completed_at).toLocaleDateString()
                            : null
                        }
                      />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard
                    title="Counsellor pool"
                    action={
                      campaign.status === CareCallbackCampaignStatus.COMPLETED ||
                      campaign.status === CareCallbackCampaignStatus.ARCHIVED ? undefined : (
                        <Button size="sm" variant="outline" className="h-6 px-2 text-xs" onClick={onEditPool}>
                          Edit
                        </Button>
                      )
                    }
                  >
                    {campaign.counsellor_pool.length === 0 ? (
                      <p className="text-xs text-fg/55">No counsellors assigned.</p>
                    ) : (
                      <ul className="space-y-1.5">
                        {campaign.counsellor_pool.map((id) => (
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
              inProgressCount={inProgressCount}
              crisisCount={crisisCount}
              onActivate={onActivate}
              onComplete={onComplete}
              onArchive={onArchive}
              onEnrol={onEnrol}
              actionLoading={actionLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}
