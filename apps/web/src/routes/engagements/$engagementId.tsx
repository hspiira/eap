import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { AlertTriangle, ArrowLeft, Briefcase } from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { engagementsApi } from "@/api/endpoints/engagements"
import { BackButton } from "@/components/common/BackButton"
import { DetailCard, DetailGrid, DetailRow } from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import {
  DeliverablesPanel,
  DetailRail,
  Hero,
  HoursPanel,
  SummaryPanel,
} from "@/components/engagements/EngagementDetailWidgets"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useBackTo } from "@/hooks/useBackTo"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { defaultErrorMessage, normalizeErrorMessage } from "@/lib/errors"
import { formatDate, formatDateTime } from "@/lib/format"
import { useEntityMutation } from "@/lib/queries"
import { EngagementStatusPill, isOverdue } from "@/routes/engagements/index"
import type { EngagementStatusValue } from "@/types/entities"

export const Route = createFileRoute("/engagements/$engagementId")({
  component: EngagementDetailPage,
})

type TabValue = "overview" | "deliverables" | "hours" | "summary"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "deliverables", "hours", "summary"]

function EngagementDetailPage() {
  const { engagementId } = Route.useParams()
  const back = useBackTo("/engagements")
  const { showSuccess, showError } = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")

  const engagementQuery = useQuery({
    queryKey: ["engagements", "detail", engagementId],
    queryFn: () => engagementsApi.getById(engagementId),
  })
  const summaryQuery = useQuery({
    queryKey: ["engagements", "summary", engagementId],
    queryFn: () => engagementsApi.getSummary(engagementId),
  })

  const clientId = engagementQuery.data?.client_id
  const clientQuery = useQuery({
    queryKey: ["clients", "detail", clientId ?? ""],
    queryFn: () => clientsApi.getById(clientId as string),
    enabled: !!clientId,
  })

  const transitionMutation = useEntityMutation({
    resource: "engagements",
    mutationFn: (to: EngagementStatusValue) => engagementsApi.transition(engagementId, to),
    detailId: engagementId,
    invalidateKeys: [["engagements", "summary", engagementId]],
    onSuccess: (e) => showSuccess(`Status: ${e.status}`),
    onError: (err) => showError(defaultErrorMessage(err)),
  })

  if (engagementQuery.isPending) {
    return (
      <PageShell icon={Briefcase} breadcrumb="Commercial · Engagements · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <DetailSkeleton />
        </div>
      </PageShell>
    )
  }
  if (!engagementQuery.data) {
    return (
      <PageShell icon={Briefcase} breadcrumb="Commercial · Engagements · Not found">
        <EmptyState
          icon={Briefcase}
          title="Engagement not found"
          description="It may have been cancelled or never existed."
          action={
            <Button variant="outline" size="sm" className="gap-1.5" onClick={back}>
              <ArrowLeft className="size-4" />
              Back to engagements
            </Button>
          }
        />
      </PageShell>
    )
  }

  const engagement = engagementQuery.data
  const allowed = engagementsApi.allowedTransitions(engagement.status)
  const client = clientQuery.data ?? null
  const overdue = isOverdue(engagement.period_end, engagement.status)
  const summaryError = summaryQuery.isError
    ? normalizeErrorMessage(summaryQuery.error, "Failed to load the summary")
    : null

  return (
    <PageShell
      icon={Briefcase}
      breadcrumb={`Commercial · Engagements · ${engagement.name}`}
      actions={<BackButton to="/engagements" label="Back to engagements" />}
    >
      <Hero engagement={engagement} client={client} overdue={overdue} />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg" data-scroll-restoration-id="detail">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="deliverables" count={engagement.deliverables.length}>
                  Deliverables
                </Tab>
                <Tab value="hours" count={engagement.hours_log.length}>
                  Hours
                </Tab>
                <Tab value="summary">Summary</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Identity">
                    <DetailGrid>
                      <DetailRow label="Name" value={engagement.name} fullWidth />
                      <DetailRow label="Description" value={engagement.description} fullWidth />
                      <DetailRow
                        label="Status"
                        value={<EngagementStatusPill status={engagement.status} />}
                      />
                      <DetailRow label="Created by" value={engagement.created_by} />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Period">
                    <DetailGrid>
                      <DetailRow label="Start" value={formatDate(engagement.period_start)} />
                      <DetailRow label="End" value={formatDate(engagement.period_end)} />
                    </DetailGrid>
                    {overdue ? (
                      <p className="mt-3 inline-flex items-center gap-1 rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[11px] font-medium text-amber-600">
                        <AlertTriangle className="size-3" />
                        Overdue: past the period end and not yet delivered
                      </p>
                    ) : null}
                  </DetailCard>

                  <DetailCard title="Lifecycle">
                    <DetailGrid>
                      <DetailRow
                        label="Activated"
                        value={
                          engagement.activated_at ? formatDateTime(engagement.activated_at) : null
                        }
                      />
                      <DetailRow
                        label="Delivered"
                        value={
                          engagement.delivered_at ? formatDateTime(engagement.delivered_at) : null
                        }
                      />
                      <DetailRow
                        label="Invoiced"
                        value={
                          engagement.invoiced_at ? formatDateTime(engagement.invoiced_at) : null
                        }
                      />
                      <DetailRow
                        label="Closed"
                        value={engagement.closed_at ? formatDateTime(engagement.closed_at) : null}
                      />
                    </DetailGrid>
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="deliverables">
                <DeliverablesPanel
                  engagementId={engagementId}
                  deliverables={engagement.deliverables}
                />
              </TabPanel>

              <TabPanel value="hours">
                <HoursPanel engagementId={engagementId} entries={engagement.hours_log} />
              </TabPanel>

              <TabPanel value="summary">
                <SummaryPanel
                  summary={summaryQuery.data ?? null}
                  loading={summaryQuery.isPending}
                  error={summaryError}
                  onRetry={() => void summaryQuery.refetch()}
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              engagement={engagement}
              client={client}
              allowedTransitions={allowed}
              transitioning={transitionMutation.isPending}
              onTransition={(to) => transitionMutation.mutate(to)}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}
