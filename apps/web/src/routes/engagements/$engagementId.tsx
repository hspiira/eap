
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowLeft,
  Briefcase,
  Users,
} from "lucide-react"

import { clientsApi } from "@/api/endpoints/clients"
import { engagementsApi } from "@/api/endpoints/engagements"
import { usersApi } from "@/api/endpoints/users"
import {
  DetailCard,
  DetailGrid,
  DetailRow,
} from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import {
  DeliverablesPanel,
  DetailRail,
  Hero,
  HoursPanel,
  TimelinePanel,
} from "@/components/engagements/EngagementDetailWidgets"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { defaultErrorMessage } from "@/lib/errors"
import { useEntityMutation } from "@/lib/queries"
import { cn } from "@/lib/utils"
import {
  EngagementStatusPill,
  isOverdue,
} from "@/routes/engagements/index"
import {
  type EngagementStatus
} from "@/types/enums"

export const Route = createFileRoute("/engagements/$engagementId")({
  component: EngagementDetailPage,
})

type TabValue = "overview" | "deliverables" | "hours" | "timeline"
const TAB_VALUES: ReadonlyArray<TabValue> = [
  "overview",
  "deliverables",
  "hours",
  "timeline",
]

function EngagementDetailPage() {
  const { engagementId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")

  const engagementQuery = useQuery({
    queryKey: ["engagements", "detail", engagementId],
    queryFn: () => engagementsApi.getById(engagementId),
  })
  const deliverablesQuery = useQuery({
    queryKey: ["engagements", "deliverables", engagementId],
    queryFn: () => engagementsApi.listDeliverables(engagementId),
  })
  const timeQuery = useQuery({
    queryKey: ["engagements", "time", engagementId],
    queryFn: () => engagementsApi.listTimeEntries(engagementId),
  })
  const timelineQuery = useQuery({
    queryKey: ["engagements", "timeline", engagementId],
    queryFn: () => engagementsApi.getTimeline(engagementId),
  })

  const clientId = engagementQuery.data?.client_id
  const clientQuery = useQuery({
    queryKey: ["clients", "detail", clientId ?? ""],
    queryFn: () => clientsApi.getById(clientId as string),
    enabled: !!clientId,
  })

  const leadId = engagementQuery.data?.lead_user_id
  const leadQuery = useQuery({
    queryKey: ["users", "detail", leadId ?? ""],
    queryFn: () => usersApi.getById(leadId as string),
    enabled: !!leadId,
  })

  const transitionMutation = useEntityMutation({
    resource: "engagements",
    mutationFn: (to: EngagementStatus) => engagementsApi.transition(engagementId, to),
    detailId: engagementId,
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
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => navigate({ to: "/engagements" })}
            >
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
  const deliverables = deliverablesQuery.data ?? []
  const timeEntries = timeQuery.data ?? []
  const timeline = timelineQuery.data ?? []
  const client = clientQuery.data ?? null
  const lead = leadQuery.data ?? null
  const overdue = isOverdue(engagement.due_date, engagement.status)
  const budgetPct = engagement.budget_hours
    ? Math.round((engagement.hours_logged / engagement.budget_hours) * 100)
    : null
  const budgetExceeded = budgetPct !== null && budgetPct > 100

  return (
    <PageShell
      icon={Briefcase}
      breadcrumb={`Commercial · Engagements · ${engagement.name}`}
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: "/engagements" })}
            aria-label="Back to engagements"
            title="Back to engagements"
            className="size-7 p-0 text-fg/70"
          >
            <ArrowLeft className="size-3.5" />
          </Button>
        </>
      }
    >
      <Hero engagement={engagement} client={client} overdue={overdue} />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="deliverables" count={deliverables.length}>
                  Deliverables
                </Tab>
                <Tab value="hours" count={timeEntries.length}>
                  Hours
                </Tab>
                <Tab value="timeline">Timeline</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Identity">
                    <DetailGrid>
                      <DetailRow label="Name" value={engagement.name} fullWidth />
                      <DetailRow
                        label="Description"
                        value={engagement.description}
                        fullWidth
                      />
                      <DetailRow label="Type" value={engagement.engagement_type} />
                      <DetailRow
                        label="Status"
                        value={<EngagementStatusPill status={engagement.status} />}
                      />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Schedule">
                    <DetailGrid>
                      <DetailRow
                        label="Start"
                        value={new Date(engagement.start_date).toLocaleDateString()}
                      />
                      <DetailRow
                        label="Due"
                        value={
                          engagement.due_date
                            ? new Date(engagement.due_date).toLocaleDateString()
                            : null
                        }
                      />
                      <DetailRow
                        label="Closed"
                        value={
                          engagement.closed_at
                            ? new Date(engagement.closed_at).toLocaleDateString()
                            : null
                        }
                      />
                    </DetailGrid>
                    {overdue ? (
                      <p className="mt-3 inline-flex items-center gap-1 rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[11px] font-medium text-amber-600">
                        <AlertTriangle className="size-3" />
                        Overdue — past due date and not yet delivered
                      </p>
                    ) : null}
                  </DetailCard>

                  <DetailCard title="Commercials">
                    <DetailGrid>
                      <DetailRow
                        label="Hourly rate"
                        value={
                          engagement.hourly_rate != null
                            ? `${engagement.currency ?? ""} ${engagement.hourly_rate.toLocaleString()}`.trim()
                            : null
                        }
                      />
                      <DetailRow
                        label="Budget"
                        value={
                          engagement.budget_hours
                            ? `${engagement.budget_hours}h`
                            : "Open-ended"
                        }
                      />
                      <DetailRow
                        label="Logged"
                        value={`${engagement.hours_logged.toFixed(1)}h`}
                      />
                      <DetailRow
                        label="Utilisation"
                        value={
                          budgetPct !== null ? (
                            <span
                              className={cn(
                                budgetExceeded ? "text-amber-600" : "text-fg",
                              )}
                            >
                              {budgetPct}%
                            </span>
                          ) : null
                        }
                      />
                    </DetailGrid>
                    {budgetPct !== null ? (
                      <div
                        className="mt-3 h-1 w-full overflow-hidden rounded-sm bg-fg/10"
                        aria-hidden
                      >
                        <div
                          className={cn(
                            "h-full",
                            budgetExceeded ? "bg-amber-500" : "bg-primary",
                          )}
                          style={{ width: `${Math.min(100, budgetPct)}%` }}
                        />
                      </div>
                    ) : null}
                  </DetailCard>

                  <DetailCard title="Lead">
                    {lead ? (
                      <Link
                        to="/users/$userId"
                        params={{ userId: lead.id }}
                        className="flex items-center gap-2.5 rounded-sm border border-fg/10 bg-bg px-3 py-2 transition-colors hover:border-fg/25"
                      >
                        <span
                          aria-hidden
                          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
                        >
                          <Users className="size-3.5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg">
                            {lead.email}
                          </p>
                        </div>
                      </Link>
                    ) : (
                      <p className="text-xs text-fg/55">No lead assigned.</p>
                    )}
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="deliverables">
                <DeliverablesPanel
                  engagementId={engagementId}
                  deliverables={deliverables}
                  loading={deliverablesQuery.isPending}
                />
              </TabPanel>

              <TabPanel value="hours">
                <HoursPanel
                  engagementId={engagementId}
                  deliverables={deliverables}
                  entries={timeEntries}
                  loading={timeQuery.isPending}
                />
              </TabPanel>

              <TabPanel value="timeline">
                <TimelinePanel timeline={timeline} loading={timelineQuery.isPending} />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              engagement={engagement}
              client={client}
              budgetPct={budgetPct}
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

