/**
 * Home dashboard. One aggregate query drives everything: delivery KPIs and
 * trend, utilisation by client and category, the import backlog, and the
 * data-quality queues. The onboarding checklist appears only for a tenant
 * with no clients yet.
 */

import { Link } from "@tanstack/react-router"
import {
  ArrowUpRight,
  Building2,
  CalendarClock,
  ClipboardList,
  FileSignature,
  Plus,
  UserCheck,
  Users,
} from "lucide-react"

import { BarList } from "@/components/dashboard/BarList"
import { DataQualityCard } from "@/components/dashboard/DataQualityCard"
import { ImportHealthCard } from "@/components/dashboard/ImportHealthCard"
import { SessionsTrendCard } from "@/components/dashboard/SessionsTrendCard"
import { type StatSpec,StatStrip } from "@/components/dashboard/StatStrip"
import { OnboardingProgressCard } from "@/components/OnboardingProgressCard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatDelta, formatKpi, useDashboard, useOnboardingCounts } from "@/lib/dashboard"

interface QuickAction {
  to: string
  label: string
  icon: React.ElementType
  description: string
}

const QUICK_ACTIONS: ReadonlyArray<QuickAction> = [
  {
    to: "/clients/new",
    label: "Add client",
    icon: Building2,
    description: "Onboard a new client organisation.",
  },
  {
    to: "/members?new=true",
    label: "Add member",
    icon: Users,
    description: "Add a covered employee or beneficiary.",
  },
  {
    to: "/service-sessions/new",
    label: "Log session",
    icon: CalendarClock,
    description: "Record a delivered care session.",
  },
  {
    to: "/contracts/new",
    label: "New contract",
    icon: FileSignature,
    description: "Draft a master service agreement.",
  },
]

export function DashboardMain() {
  const dashboard = useDashboard()
  const data = dashboard.data
  const loading = dashboard.isLoading
  const error = dashboard.isError

  const kpis = data?.kpis
  const stats: ReadonlyArray<StatSpec> = [
    {
      id: "sessions",
      label: "Sessions, 90 days",
      value: formatKpi(kpis?.sessions_90d ?? null),
      icon: CalendarClock,
      tone: "success",
      delta: kpis ? (formatDelta(kpis.sessions_90d, kpis.sessions_prior_90d) ?? undefined) : undefined,
      hint: "Completed sessions delivered",
      spark: data?.sessions_monthly.map((m) => m.total),
      loading,
      error,
    },
    {
      id: "clients-served",
      label: "Clients served",
      value: formatKpi(kpis?.clients_served_90d ?? null),
      icon: Building2,
      tone: "info",
      hint: kpis ? `of ${kpis.clients_total} clients, last 90 days` : undefined,
      loading,
      error,
    },
    {
      id: "covered-members",
      label: "Covered members",
      value: formatKpi(kpis?.covered_members ?? null),
      icon: UserCheck,
      tone: "info",
      hint: kpis
        ? `${kpis.clients_with_roster} of ${kpis.clients_total} clients have a roster`
        : undefined,
      loading,
      error,
    },
    {
      id: "import-backlog",
      label: "Import backlog",
      value: formatKpi(kpis?.import_backlog ?? null),
      icon: ClipboardList,
      tone: "warning",
      hint: data?.import_batch
        ? `rows in ${data.import_batch.file_name} awaiting resolution`
        : undefined,
      loading,
      error,
    },
  ]

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-bg">
      <div className="grid w-full gap-4 p-4 md:p-6">
        <DashboardHeader />
        <StatStrip stats={stats} />
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="grid content-start gap-4 lg:col-span-2">
            <SessionsTrendCard
              monthly={data?.sessions_monthly ?? []}
              loading={loading}
              error={error}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <TopClientsCard data={data} loading={loading} />
              <CategoryCard data={data} loading={loading} />
            </div>
            <ImportHealthCard
              batch={data?.import_batch}
              queues={data?.import_queues ?? []}
              loading={loading}
            />
          </div>
          <div className="grid content-start gap-4">
            <QuickActionsCard actions={QUICK_ACTIONS} />
            <DataQualityCard quality={data?.data_quality} loading={loading} />
            {kpis && kpis.clients_total === 0 ? <EmptyTenantOnboarding /> : null}
          </div>
        </div>
      </div>
    </div>
  )
}

function DashboardHeader() {
  return (
    <div className="flex flex-wrap items-end justify-between gap-2">
      <div className="grid gap-0.5">
        <h1 className="text-xl font-semibold text-fg">Welcome back</h1>
        <p className="text-sm text-fg-muted">Here's what's happening across your tenant today.</p>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link to="/service-sessions">
            View sessions
            <ArrowUpRight className="size-3.5" />
          </Link>
        </Button>
        <Button size="sm" asChild>
          <Link to="/service-sessions/new">
            <Plus className="size-3.5" />
            Log session
          </Link>
        </Button>
      </div>
    </div>
  )
}

function TopClientsCard({
  data,
  loading,
}: {
  data: ReturnType<typeof useDashboard>["data"]
  loading: boolean
}) {
  const items =
    data?.top_clients.map((client) => ({
      key: client.client_id,
      label: client.client_name,
      value: client.total,
      to: "/clients/$clientId",
      params: { clientId: client.client_id },
    })) ?? []
  return (
    <ListCard
      title="Sessions by client"
      subtitle="Last 12 months"
      loading={loading}
      empty={items.length === 0 ? "No sessions recorded yet." : undefined}
    >
      <BarList items={items} />
    </ListCard>
  )
}

function CategoryCard({
  data,
  loading,
}: {
  data: ReturnType<typeof useDashboard>["data"]
  loading: boolean
}) {
  const items =
    data?.sessions_by_category.map((category) => ({
      key: category.category,
      label: category.category,
      value: category.total,
    })) ?? []
  return (
    <ListCard
      title="Sessions by category"
      subtitle="Last 12 months"
      loading={loading}
      empty={items.length === 0 ? "No categorised sessions yet." : undefined}
    >
      <BarList items={items} />
    </ListCard>
  )
}

function ListCard({
  title,
  subtitle,
  loading,
  empty,
  children,
}: {
  title: string
  subtitle: string
  loading: boolean
  empty?: string
  children: React.ReactNode
}) {
  return (
    <Card className="rounded-md">
      <CardHeader className="border-b border-border p-3">
        <CardTitle className="text-sm font-semibold text-fg">{title}</CardTitle>
        <p className="text-xs text-fg-muted">{subtitle}</p>
      </CardHeader>
      <CardContent className="p-3">
        {loading ? (
          <div className="grid gap-2">
            <div className="h-8 animate-pulse rounded bg-muted" />
            <div className="h-8 animate-pulse rounded bg-muted" />
          </div>
        ) : empty ? (
          <p className="py-2 text-sm text-fg-muted">{empty}</p>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  )
}

function QuickActionsCard({ actions }: { actions: ReadonlyArray<QuickAction> }) {
  return (
    <Card className="rounded-md">
      <CardHeader className="border-b border-border p-3">
        <CardTitle className="text-sm font-semibold text-fg">Quick actions</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {actions.map((action, i) => (
          <Link
            key={action.to}
            to={action.to}
            className={
              "group flex items-start gap-3 p-3 transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none" +
              (i > 0 ? " border-t border-border-subtle" : "")
            }
          >
            <span
              className="flex size-8 shrink-0 items-center justify-center rounded-md bg-muted text-fg-muted transition-colors group-hover:bg-primary/10 group-hover:text-primary"
              aria-hidden
            >
              <action.icon className="size-4" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1 text-sm font-medium text-fg">
                {action.label}
                <ArrowUpRight className="size-3.5 shrink-0 text-fg-subtle transition-colors group-hover:text-primary" />
              </div>
              <p className="text-xs text-fg-muted">{action.description}</p>
            </div>
          </Link>
        ))}
      </CardContent>
    </Card>
  )
}

function EmptyTenantOnboarding() {
  const counts = useOnboardingCounts(true)
  const steps = [
    { id: 1, label: "Add first client", done: false },
    { id: 2, label: "Create a service", done: (counts.services ?? 0) > 0 },
    { id: 3, label: "Assign a service to a client", done: (counts.assignments ?? 0) > 0 },
    { id: 4, label: "Record a contract", done: (counts.contracts ?? 0) > 0 },
  ]
  return <OnboardingProgressCard steps={steps} />
}
