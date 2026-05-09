import { useCallback, useEffect, useState } from "react"

import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  CalendarClock,
  ChevronRight,
  Pencil,
  Plus,
  RotateCw,
  Wrench,
} from "lucide-react"

import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { EmptyState } from "@/components/common/EmptyState"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Tab, TabPanel, Tabs, TabsList } from "@/components/common/Tabs"
import { humanizeServiceType, ServiceFormSheet } from "@/components/ServiceFormSheet"
import { DetailSkeleton } from "@/components/common/PageSkeletons"
import { Button } from "@/components/ui/button"
import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useTabSearchParam } from "@/hooks/useTabSearchParam"
import { cn } from "@/lib/utils"
import type { Service, ServiceAssignment, ServiceSession } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/services/$serviceId")({
  component: ServiceDetailPage,
})

type TabValue = "overview" | "contracts" | "sessions" | "history"
const TAB_VALUES: ReadonlyArray<TabValue> = ["overview", "contracts", "sessions", "history"]

function ServiceDetailPage() {
  const { serviceId } = Route.useParams()
  const navigate = useNavigate()
  const [service, setService] = useState<Service | null>(null)
  const [assignments, setAssignments] = useState<ServiceAssignment[]>([])
  const [assignmentsLoading, setAssignmentsLoading] = useState(false)
  const [sessions, setSessions] = useState<ServiceSession[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [tab, setTab] = useTabSearchParam<TabValue>(TAB_VALUES, "overview")
  const [editOpen, setEditOpen] = useState(false)

  const fetchService = useCallback(async () => {
    try {
      setLoading(true)
      setService(await servicesApi.getById(serviceId))
    } catch {
      setService(null)
    } finally {
      setLoading(false)
    }
  }, [serviceId])

  useEffect(() => {
    fetchService()
  }, [fetchService])

  useEffect(() => {
    setAssignmentsLoading(true)
    serviceAssignmentsApi
      .list({
        limit: 50,
        ...({ service_id: serviceId } as Record<string, unknown>),
      })
      .then((res) =>
        setAssignments(
          (res.items ?? []).filter((a) => a.service_id === serviceId),
        ),
      )
      .catch(() => setAssignments([]))
      .finally(() => setAssignmentsLoading(false))
  }, [serviceId])

  useEffect(() => {
    setSessionsLoading(true)
    serviceSessionsApi
      .list({
        limit: 20,
        ...({ service_id: serviceId } as Record<string, unknown>),
      })
      .then((res) =>
        setSessions((res.items ?? []).filter((s) => s.service_id === serviceId)),
      )
      .catch(() => setSessions([]))
      .finally(() => setSessionsLoading(false))
  }, [serviceId])

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        if (action === "activate") await servicesApi.activate(id)
        else if (action === "deactivate") await servicesApi.deactivate(id)
        else if (action === "archive") await servicesApi.archive(id)
        else if (action === "restore") await servicesApi.restore(id)
        await fetchService()
      } finally {
        setActionLoading(false)
      }
    },
    [fetchService],
  )

  if (loading) {
    return (
      <PageShell icon={Wrench} breadcrumb="Catalog · Services · …">
        <div className="min-h-0 flex-1 overflow-auto p-5">
          <DetailSkeleton />
        </div>
      </PageShell>
    )
  }

  if (!service) {
    return (
      <PageShell icon={Wrench} breadcrumb="Catalog · Services · Not found">
        <EmptyState
          icon={Wrench}
          title="Service not found"
          description="It may have been archived or doesn't exist."
          action={
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => navigate({ to: "/services" })}
            >
              <ArrowLeft className="size-4" />
              Back to services
            </Button>
          }
        />
      </PageShell>
    )
  }

  return (
    <PageShell
      icon={Wrench}
      breadcrumb={`Catalog · Services · ${service.name}`}
      actions={
        <>
          <button
            type="button"
            onClick={() => navigate({ to: "/services" })}
            aria-label="Back to services"
            title="Back to services"
            className="grid size-7 place-items-center rounded-sm text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
          >
            <ArrowLeft className="size-3.5" />
          </button>
          <button
            type="button"
            onClick={fetchService}
            aria-label="Refresh"
            title="Refresh"
            className="grid size-7 place-items-center rounded-sm text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
          >
            <RotateCw className="size-3.5" />
          </button>
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 px-2.5"
            onClick={() => setEditOpen(true)}
          >
            <Pencil className="size-3.5" />
            Edit
          </Button>
        </>
      }
    >
      <Hero service={service} />

      <ServiceFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        service={service}
        onSaved={(updated) => setService(updated)}
      />

      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="grid grid-cols-12 gap-5 px-5 py-5">
          <div className="col-span-12 min-w-0 lg:col-span-8">
            <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
              <TabsList className="-mx-3 mb-4 px-3">
                <Tab value="overview">Overview</Tab>
                <Tab value="contracts" count={assignments.length}>
                  Contracts
                </Tab>
                <Tab value="sessions" count={sessions.length}>
                  Sessions
                </Tab>
                <Tab value="history">History</Tab>
              </TabsList>

              <TabPanel value="overview">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <DetailCard title="Identity">
                    <DetailGrid>
                      <DetailRow label="Name" value={service.name} fullWidth />
                      <DetailRow label="Description" value={service.description} fullWidth />
                      <DetailRow
                        label="Type"
                        value={
                          service.service_type
                            ? humanizeServiceType(service.service_type)
                            : null
                        }
                      />
                      <DetailRow label="Category" value={service.category} />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Defaults">
                    <DetailGrid>
                      <DetailRow
                        label="Duration"
                        value={
                          service.duration_minutes != null
                            ? `${service.duration_minutes} min`
                            : null
                        }
                      />
                      <DetailRow label="Status" value={<StatusBadge status={service.status} />} />
                    </DetailGrid>
                  </DetailCard>

                  <DetailCard title="Group settings">
                    <DetailGrid>
                      <DetailRow
                        label="Allow group sessions"
                        value={service.group_settings?.allow_group_sessions ? "Yes" : "No"}
                      />
                      <DetailRow
                        label="Min group size"
                        value={service.group_settings?.min_group_size}
                      />
                      <DetailRow
                        label="Max group size"
                        value={service.group_settings?.max_group_size}
                      />
                    </DetailGrid>
                  </DetailCard>
                </div>
              </TabPanel>

              <TabPanel value="contracts">
                <ContractsPanel assignments={assignments} loading={assignmentsLoading} />
              </TabPanel>

              <TabPanel value="sessions">
                <SessionsPanel
                  sessions={sessions}
                  loading={sessionsLoading}
                  serviceId={serviceId}
                />
              </TabPanel>

              <TabPanel value="history">
                <EmptyState
                  title="No activity yet"
                  description="Catalog changes and lifecycle events will appear here once the audit feed is wired up."
                />
              </TabPanel>
            </Tabs>
          </div>

          <aside className="col-span-12 min-w-0 lg:col-span-4 lg:pt-14">
            <DetailRail
              service={service}
              assignmentsCount={assignments.length}
              sessionsCount={sessions.length}
              onAction={handleAction}
              actionLoading={actionLoading}
            />
          </aside>
        </div>
      </div>
    </PageShell>
  )
}

function Hero({ service }: { service: Service }) {
  return (
    <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-3">
      <span
        aria-hidden
        className="grid size-9 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <Wrench className="size-4" />
      </span>
      <h1 className="shrink truncate text-base font-semibold leading-tight text-fg">
        {service.name}
      </h1>
      {service.service_type ? (
        <span className="font-mono text-xs text-fg/55">
          {humanizeServiceType(service.service_type)}
        </span>
      ) : null}
      <span className="h-4 w-px shrink-0 bg-fg/15" aria-hidden />
      <StatusBadge status={service.status} />
      {service.duration_minutes != null ? (
        <span className="font-mono text-xs text-fg/55">
          {service.duration_minutes}m
        </span>
      ) : null}
    </div>
  )
}

function ContractsPanel({
  assignments,
  loading,
}: {
  assignments: ServiceAssignment[]
  loading: boolean
}) {
  if (loading) return <p className="text-sm text-fg/65">Loading…</p>
  if (assignments.length === 0) {
    return (
      <EmptyState
        title="Not on any contract yet"
        description="Add this service to a contract from the contract detail page."
      />
    )
  }
  return (
    <div className="overflow-hidden border border-fg/10 bg-surface">
      <table className="w-full caption-bottom text-sm">
        <TableHeader className="border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
          <TableRow className="border-fg/8 hover:bg-transparent">
            <TableHead>Contract</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Start</TableHead>
            <TableHead>End</TableHead>
            <TableHead className="w-10 text-right text-fg/65">
              <span className="sr-only">Open</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {assignments.map((a) => (
            <TableRow key={a.id} className="group border-fg/8">
              <TableCell>
                <Link
                  to="/contracts/$contractId"
                  params={{ contractId: a.contract_id }}
                  className="font-mono text-sm text-fg group-hover:text-primary"
                >
                  {a.contract_id.slice(0, 8)}
                </Link>
              </TableCell>
              <TableCell>
                <StatusBadge status={a.status} />
              </TableCell>
              <TableCell className="text-sm text-fg/75">{a.start_date ?? "—"}</TableCell>
              <TableCell className="text-sm text-fg/75">{a.end_date ?? "—"}</TableCell>
              <TableCell className="text-right">
                <Link
                  to="/service-assignments/$assignmentId"
                  params={{ assignmentId: a.id }}
                  aria-label="Open assignment"
                  className="inline-grid size-7 place-items-center rounded-sm text-fg/55 hover:bg-surface-hover hover:text-fg"
                >
                  <ChevronRight className="size-3.5" />
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </table>
    </div>
  )
}

function SessionsPanel({
  sessions,
  loading,
  serviceId,
}: {
  sessions: ServiceSession[]
  loading: boolean
  serviceId: string
}) {
  if (loading) return <p className="text-sm text-fg/65">Loading…</p>
  if (sessions.length === 0) {
    return (
      <EmptyState
        title="No sessions yet"
        description="Sessions delivered against this service will show up here."
        action={
          <Link
            to="/service-sessions"
            search={{ new: true, service_id: serviceId }}
            className="inline-flex h-9 items-center gap-1.5 rounded-sm border border-fg/15 bg-surface px-3 text-sm font-medium text-fg hover:bg-surface-hover"
          >
            <Plus className="size-4" />
            Schedule session
          </Link>
        }
      />
    )
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-fg/55">{sessions.length} recent sessions.</p>
        <Link
          to="/service-sessions"
          search={{ service_id: serviceId }}
          className="text-xs font-medium text-primary hover:underline"
        >
          View all
        </Link>
      </div>
      <div className="overflow-hidden border border-fg/10 bg-surface">
        <table className="w-full caption-bottom text-sm">
          <TableHeader className="border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
            <TableRow className="border-fg/8 hover:bg-transparent">
              <TableHead>Scheduled</TableHead>
              <TableHead>Person</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-10 text-right text-fg/65">
                <span className="sr-only">Open</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sessions.slice(0, 10).map((s) => (
              <TableRow key={s.id} className="group border-fg/8">
                <TableCell className="text-sm text-fg">
                  {new Date(s.scheduled_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Link
                    to="/persons/$personId"
                    params={{ personId: s.person_id }}
                    className="font-mono text-xs text-fg/75 hover:text-primary"
                  >
                    {s.person_id.slice(0, 8)}
                  </Link>
                </TableCell>
                <TableCell>
                  <StatusBadge status={s.status} />
                </TableCell>
                <TableCell className="text-right">
                  <Link
                    to="/service-sessions/$sessionId"
                    params={{ sessionId: s.id }}
                    aria-label="Open session"
                    className="inline-grid size-7 place-items-center rounded-sm text-fg/55 hover:bg-surface-hover hover:text-fg"
                  >
                    <ChevronRight className="size-3.5" />
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </table>
      </div>
    </div>
  )
}

interface DetailRailProps {
  service: Service
  assignmentsCount: number
  sessionsCount: number
  onAction: (id: string, action: LifecycleAction) => Promise<void>
  actionLoading: boolean
}

function DetailRail({
  service,
  assignmentsCount,
  sessionsCount,
  onAction,
  actionLoading,
}: DetailRailProps) {
  return (
    <div className="space-y-5">
      <RailSection title="At a glance">
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Contracts" value={assignmentsCount} />
          <Stat label="Sessions" value={sessionsCount} />
        </div>
      </RailSection>

      <RailSection title="Defaults">
        <DetailGrid>
          <DetailRow
            label="Duration"
            value={
              service.duration_minutes != null
                ? `${service.duration_minutes}m`
                : null
            }
          />
          <DetailRow
            label="Group"
            value={service.group_settings?.allow_group_sessions ? "Allowed" : "Individual"}
          />
        </DetailGrid>
      </RailSection>

      <RailSection title="Lifecycle">
        <LifecycleActions
          entityId={service.id}
          currentStatus={service.status}
          kind="service"
          onAction={onAction}
          loading={actionLoading}
        />
      </RailSection>

      <RailSection title="Quick actions">
        <Link
          to="/service-sessions"
          search={{ new: true, service_id: service.id }}
          className="inline-flex h-8 w-full items-center justify-center gap-1.5 rounded-sm border border-fg/15 bg-bg text-sm text-fg hover:bg-surface-hover"
        >
          <CalendarClock className="size-3.5" />
          Schedule session
        </Link>
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
