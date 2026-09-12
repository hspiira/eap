/**
 * Home dashboard. One aggregate query drives everything.
 *
 * The page leads with decisions: what is blocked and what to do about it.
 * The analytics below answer "how is delivery going", all scoped by a single
 * window control that sits above them.
 */

import { useMemo, useState } from "react"

import { Link } from "@tanstack/react-router"
import {
  ArrowUpRight,
  Banknote,
  Building2,
  CalendarClock,
  ClipboardList,
  Gauge,
  Plus,
  UserCheck,
} from "lucide-react"

import { AttentionCard, buildAttentionItems } from "@/components/dashboard/AttentionCard"
import { CardDelta } from "@/components/dashboard/CardBar"
import { CategoryDonutCard } from "@/components/dashboard/CategoryDonutCard"
import { OutcomeMixCard } from "@/components/dashboard/OutcomeMixCard"
import { RangeFilter } from "@/components/dashboard/RangeFilter"
import { SessionsAreaCard } from "@/components/dashboard/SessionsAreaCard"
import { type StatSpec, StatStrip } from "@/components/dashboard/StatStrip"
import { TopClientsCard } from "@/components/dashboard/TopClientsCard"
import { UpcomingBookingsCard } from "@/components/dashboard/UpcomingBookingsCard"
import { OnboardingProgressCard } from "@/components/OnboardingProgressCard"
import { Button } from "@/components/ui/button"
import {
  type DashboardRange,
  DEFAULT_RANGE,
  formatDelta,
  formatKpi,
  rangeLabel,
  useDashboard,
  useOnboardingCounts,
} from "@/lib/dashboard"
import {
  outcomeInsight,
  sessionsInsight,
  upcomingInsight,
  utilizationPerThousand,
  valueHint,
} from "@/lib/dashboard-insights"

export function DashboardMain() {
  const [range, setRange] = useState<DashboardRange>(DEFAULT_RANGE)
  const dashboard = useDashboard(range)
  const data = dashboard.data
  const loading = dashboard.isLoading
  const error = dashboard.isError
  const refreshing = dashboard.isFetching && !dashboard.isLoading

  const attention = useMemo(() => (data ? buildAttentionItems(data) : []), [data])
  const stats = useStatSpecs(data, { loading, error, range })

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-bg">
      <div className="grid w-full gap-4 p-4 md:p-6">
        <DashboardHeader />
        <StatStrip stats={stats} />

        <div className="grid gap-4 lg:grid-cols-12">
          <div className="lg:col-span-8">
            <SessionsAreaCard
              series={data?.sessions_series ?? []}
              total={data?.kpis.sessions ?? 0}
              delta={<SessionsDelta data={data} />}
              insight={data ? sessionsInsight(data) : null}
              loading={loading}
              error={error}
              refreshing={refreshing}
              control={
                <RangeFilter value={range} onChange={setRange} years={data?.session_years ?? []} />
              }
            />
          </div>
          <div className="lg:col-span-4">
            <AttentionCard items={attention} loading={loading} />
          </div>
        </div>

        <UpcomingBookingsCard
          upcoming={data?.upcoming ?? null}
          insight={data ? upcomingInsight(data.upcoming) : null}
          loading={loading}
        />

        <div className="grid gap-4 lg:grid-cols-12">
          <div className={data?.outcome_mix ? "lg:col-span-5" : "lg:col-span-7"}>
            <TopClientsCard clients={data?.top_clients ?? []} loading={loading} />
          </div>
          {data?.outcome_mix ? (
            <div className="lg:col-span-4">
              <OutcomeMixCard
                mix={data.outcome_mix}
                insight={outcomeInsight(data.outcome_mix)}
                loading={loading}
              />
            </div>
          ) : null}
          <div className={data?.outcome_mix ? "lg:col-span-3" : "lg:col-span-5"}>
            <CategoryDonutCard categories={data?.sessions_by_category ?? []} loading={loading} />
          </div>
        </div>

        {data && data.kpis.clients_total === 0 ? <EmptyTenantOnboarding /> : null}
      </div>
    </div>
  )
}

function useStatSpecs(
  data: ReturnType<typeof useDashboard>["data"],
  { loading, error, range }: { loading: boolean; error: boolean; range: DashboardRange },
): ReadonlyArray<StatSpec> {
  const kpis = data?.kpis
  const delta = kpis ? formatDelta(kpis.sessions, kpis.sessions_prior) : null
  return [
    {
      id: "sessions",
      label: "Sessions",
      value: formatKpi(kpis?.sessions ?? null),
      icon: CalendarClock,
      tone: "success",
      delta: delta ?? undefined,
      hint: rangeLabel(range),
      spark: data?.sessions_series.map((p) => p.total),
      loading,
      error,
    },
    {
      id: "clients-served",
      label: "Clients served",
      value: formatKpi(kpis?.clients_served ?? null),
      icon: Building2,
      tone: "info",
      hint: kpis ? `of ${kpis.clients_total}` : undefined,
      loading,
      error,
    },
    {
      id: "covered-members",
      label: "Covered members",
      value: formatKpi(kpis?.covered_members ?? null),
      icon: UserCheck,
      tone: "info",
      hint: kpis ? `${kpis.clients_with_roster} of ${kpis.clients_total} rostered` : undefined,
      loading,
      error,
    },
    {
      id: "utilization",
      label: "Utilization",
      value: data ? (utilizationPerThousand(data)?.toLocaleString() ?? "-") : "-",
      icon: Gauge,
      tone: "success",
      hint: "sessions per 1,000 covered",
      loading,
      error,
    },
    {
      id: "value-delivered",
      label: "Delivered value",
      value: kpis ? `UGX ${formatKpi(kpis.value_delivered_ugx)}` : "-",
      icon: Banknote,
      tone: "info",
      hint: data ? valueHint(data) : undefined,
      loading,
      error,
    },
    {
      id: "import-backlog",
      label: "Import backlog",
      value: formatKpi(kpis?.import_backlog ?? null),
      icon: ClipboardList,
      tone: "warning",
      hint: "rows blocked",
      loading,
      error,
    },
  ]
}

function SessionsDelta({ data }: { data: ReturnType<typeof useDashboard>["data"] }) {
  if (!data) return null
  const delta = formatDelta(data.kpis.sessions, data.kpis.sessions_prior)
  if (!delta) return null
  return <CardDelta label={delta.label} direction={delta.direction} tone={delta.tone} />
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
