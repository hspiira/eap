import {
  ArrowUpRight,
  Building2,
  CalendarClock,
  ClipboardCheck,
  FileSignature,
  Plus,
  Users,
} from "lucide-react"

import { Link } from "@tanstack/react-router"

import { ActivityFeedCard } from "@/components/ActivityFeedCard"
import { ClientAlertsCard, type ClientAlert } from "@/components/ClientAlertsCard"
import { OnboardingProgressCard } from "@/components/OnboardingProgressCard"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface KpiSpec {
  id: string
  label: string
  value: string
  delta?: { value: string; direction: "up" | "down"; tone: "success" | "danger" | "muted" }
  hint?: string
}

const KPIS: ReadonlyArray<KpiSpec> = [
  {
    id: "active-clients",
    label: "Active clients",
    value: "—",
    hint: "Live from API once wired",
  },
  {
    id: "open-cases",
    label: "Open cases",
    value: "—",
  },
  {
    id: "sessions-mtd",
    label: "Sessions MTD",
    value: "—",
  },
  {
    id: "renewals-30d",
    label: "Renewals (30d)",
    value: "—",
  },
]

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
    to: "/persons/new",
    label: "Add person",
    icon: Users,
    description: "Register an employee, dependent or provider.",
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

const SAMPLE_ALERTS: ClientAlert[] = [
  {
    id: "demo-a1",
    title: "Wire alerts feed",
    severity: "low",
    description:
      "Hook this card up to the audit-log API once query factories land in lib/queries.",
  },
]

export function DashboardMain() {
  return (
    <div className="flex min-h-0 flex-1 flex-col bg-bg">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 p-4 md:p-6">
        <DashboardHeader />
        <KpiStrip kpis={KPIS} />
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="grid gap-4 lg:col-span-2">
            <QuickActionsCard actions={QUICK_ACTIONS} />
            <ActivityFeedCard />
          </div>
          <div className="grid gap-4">
            <OnboardingProgressCard />
            <ClientAlertsCard alerts={SAMPLE_ALERTS} />
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
        <p className="text-sm text-fg-muted">
          Here's what's happening across your tenant today.
        </p>
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
      <CardContent className="grid grid-cols-2 gap-0 p-0 md:grid-cols-4">
        {kpis.map((kpi, i) => (
          <div
            key={kpi.id}
            className={cn(
              "p-4",
              i > 0 && "border-l border-border-subtle",
              i === 2 && "border-l-0 md:border-l",
              "border-t border-border-subtle md:border-t-0",
              i < 2 && "border-t-0",
            )}
          >
            <div className="text-xs font-medium uppercase tracking-wide text-fg-muted">
              {kpi.label}
            </div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="font-mono text-2xl font-semibold tabular-nums text-fg">
                {kpi.value}
              </span>
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
                  className="font-mono tabular-nums"
                >
                  {kpi.delta.direction === "up" ? "↑" : "↓"} {kpi.delta.value}
                </Badge>
              ) : null}
            </div>
            {kpi.hint ? (
              <p className="mt-1 text-xs text-fg-subtle">{kpi.hint}</p>
            ) : null}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function QuickActionsCard({
  actions,
}: {
  actions: ReadonlyArray<QuickAction>
}) {
  return (
    <Card className="rounded-md">
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border p-3">
        <CardTitle className="text-sm font-semibold text-fg">
          Quick actions
        </CardTitle>
        <Badge variant="outline" size="sm">
          <ClipboardCheck className="size-3" />
          {actions.length}
        </Badge>
      </CardHeader>
      <CardContent className="grid gap-0 p-0 sm:grid-cols-2">
        {actions.map((action, i) => (
          <Link
            key={action.to}
            to={action.to}
            className={cn(
              "group flex items-start gap-3 p-3 transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none",
              i > 0 && "border-t border-border-subtle",
              i === 1 && "sm:border-t-0 sm:border-l",
              i > 1 && "sm:border-l-0",
              i % 2 === 1 && "sm:border-l sm:border-l-border-subtle",
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
