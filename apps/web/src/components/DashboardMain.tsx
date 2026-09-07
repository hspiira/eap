import { useMemo } from "react"

import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowUpRight,
  Building2,
  CalendarClock,
  ClipboardCheck,
  FileSignature,
  Plus,
  Users,
} from "lucide-react"

import { ActivityFeedCard } from "@/components/ActivityFeedCard"
import { ClientAlertsCard } from "@/components/clients/ClientAlertsCard"
import { OnboardingProgressCard } from "@/components/OnboardingProgressCard"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatKpi, useDashboardKpis } from "@/lib/dashboard"
import { cn } from "@/lib/utils"

type KpiTone = "info" | "danger" | "success" | "warning"

interface KpiSpec {
  id: string
  label: string
  value: string
  icon: React.ElementType
  tone: KpiTone
  loading?: boolean
  error?: boolean
  delta?: { value: string; direction: "up" | "down"; tone: "success" | "danger" | "muted" }
  hint?: string
}

const TONE_BADGE: Record<KpiTone, string> = {
  info: "bg-info-soft text-info-fg ring-info/20",
  danger: "bg-danger-soft text-danger-fg ring-danger/20",
  success: "bg-success-soft text-success-fg ring-success/20",
  warning: "bg-warning-soft text-warning-fg ring-warning/20",
}

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
  const kpis = useDashboardKpis()

  // Derived from the same counts the KPI strip shows, so the checklist reflects
  // the tenant rather than a fixed script.
  const onboardingSteps = useMemo(
    () => [
      { id: 1, label: "Add first client", done: (kpis.clients.value ?? 0) > 0 },
      { id: 2, label: "Create a service", done: (kpis.services.value ?? 0) > 0 },
      {
        id: 3,
        label: "Assign a service to a client",
        done: (kpis.assignments.value ?? 0) > 0,
      },
      { id: 4, label: "Record a contract", done: (kpis.contracts.value ?? 0) > 0 },
    ],
    [kpis.clients.value, kpis.services.value, kpis.assignments.value, kpis.contracts.value],
  )

  const kpiSpecs: ReadonlyArray<KpiSpec> = [
    {
      id: "clients",
      label: "Clients",
      value: formatKpi(kpis.clients.value),
      icon: Building2,
      tone: "info",
      loading: kpis.clients.loading,
      error: kpis.clients.error,
    },
    {
      id: "incidents",
      label: "Incidents",
      value: formatKpi(kpis.incidents.value),
      icon: AlertTriangle,
      tone: "danger",
      loading: kpis.incidents.loading,
      error: kpis.incidents.error,
    },
    {
      id: "sessions",
      label: "Sessions",
      value: formatKpi(kpis.sessions.value),
      icon: CalendarClock,
      tone: "success",
      loading: kpis.sessions.loading,
      error: kpis.sessions.error,
    },
    {
      id: "contracts",
      label: "Contracts",
      value: formatKpi(kpis.contracts.value),
      icon: FileSignature,
      tone: "warning",
      loading: kpis.contracts.loading,
      error: kpis.contracts.error,
    },
  ]

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-bg">
      <div className="grid w-full gap-4 p-4 md:p-6">
        <DashboardHeader />
        <KpiStrip kpis={kpiSpecs} />
        <div className="grid gap-4 lg:grid-cols-3 xl:grid-cols-4">
          <div className="grid gap-4 lg:col-span-2 xl:col-span-3">
            <QuickActionsCard actions={QUICK_ACTIONS} />
            <ActivityFeedCard />
          </div>
          <div className="grid gap-4 xl:col-span-1">
            <OnboardingProgressCard steps={onboardingSteps} />
            <ClientAlertsCard alerts={[]} />
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
          <Link to="/clients">
            View clients
            <ArrowUpRight className="size-3.5" />
          </Link>
        </Button>
        <Button size="sm" asChild>
          <Link to="/clients/new">
            <Plus className="size-3.5" />
            New client
          </Link>
        </Button>
      </div>
    </div>
  )
}

function KpiStrip({ kpis }: { kpis: ReadonlyArray<KpiSpec> }) {
  return (
    <Card className="rounded-md">
      <CardContent className="flex flex-col p-0 md:flex-row">
        {kpis.map((kpi, i) => (
          <div
            key={kpi.id}
            className={cn(
              "flex flex-1 items-center gap-3 px-4 py-3",
              i > 0 && "border-t border-border-subtle md:border-l md:border-t-0",
            )}
          >
            <span
              className={cn(
                "flex size-9 shrink-0 items-center justify-center rounded-md ring-1",
                TONE_BADGE[kpi.tone],
              )}
              aria-hidden
            >
              <kpi.icon className="size-4" />
            </span>
            <span className="min-w-0 flex-1 truncate text-sm font-medium text-fg">{kpi.label}</span>
            {kpi.loading ? (
              <Skeleton className="h-6 w-10" />
            ) : kpi.error ? (
              <span
                className="text-xl font-semibold tabular-nums text-fg-subtle"
                title="Failed to load"
              >
                -
              </span>
            ) : (
              <span className="text-xl font-semibold tabular-nums text-fg">{kpi.value}</span>
            )}
            {kpi.delta ? (
              <Badge
                variant={
                  kpi.delta.tone === "success"
                    ? "secondary"
                    : kpi.delta.tone === "danger"
                      ? "destructive"
                      : "outline"
                }
                size="sm"
                className="tabular-nums"
              >
                {kpi.delta.direction === "up" ? "↑" : "↓"} {kpi.delta.value}
              </Badge>
            ) : null}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function QuickActionsCard({ actions }: { actions: ReadonlyArray<QuickAction> }) {
  return (
    <Card className="rounded-md">
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border p-3">
        <CardTitle className="text-sm font-semibold text-fg">Quick actions</CardTitle>
        <Badge variant="outline" size="sm">
          <ClipboardCheck className="size-3" />
          {actions.length}
        </Badge>
      </CardHeader>
      <CardContent className="grid gap-0 p-0 sm:grid-cols-2 xl:grid-cols-4">
        {actions.map((action) => (
          <Link
            key={action.to}
            to={action.to}
            className={cn(
              "group flex items-start gap-3 p-3 transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none",
              "border-t border-border-subtle",
              "sm:nth-[-n+2]:border-t-0 sm:nth-[2n]:border-l sm:nth-[2n]:border-l-border-subtle",
              "xl:border-t-0 xl:not-first:border-l xl:not-first:border-l-border-subtle",
            )}
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
