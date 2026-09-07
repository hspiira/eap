/**
 * Dashboard data hooks and formatting helpers.
 *
 * One aggregate query feeds the whole page. The onboarding checklist still
 * fans out to three list endpoints, but only for a tenant with no clients,
 * so a working tenant pays for exactly one request.
 */

import { useQueries, useQuery } from "@tanstack/react-query"

import { contractsApi } from "@/api/endpoints/contracts"
import { dashboardApi } from "@/api/endpoints/dashboard"
import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { servicesApi } from "@/api/endpoints/services"

import { entityListKey } from "./queries"

const KPI_PARAMS = { page: 1, limit: 1 } as const
const ONE_MINUTE = 60_000

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard", "aggregate"],
    queryFn: () => dashboardApi.get(),
    staleTime: ONE_MINUTE,
  })
}

export interface OnboardingCounts {
  services: number | null
  assignments: number | null
  contracts: number | null
}

export function useOnboardingCounts(enabled: boolean): OnboardingCounts {
  const [services, assignments, contracts] = useQueries({
    queries: [
      {
        queryKey: entityListKey("services", KPI_PARAMS),
        queryFn: () => servicesApi.list(KPI_PARAMS),
        staleTime: ONE_MINUTE,
        enabled,
      },
      {
        queryKey: entityListKey("service-assignments", KPI_PARAMS),
        queryFn: () => serviceAssignmentsApi.list(KPI_PARAMS),
        staleTime: ONE_MINUTE,
        enabled,
      },
      {
        queryKey: entityListKey("contracts", KPI_PARAMS),
        queryFn: () => contractsApi.list(KPI_PARAMS),
        staleTime: ONE_MINUTE,
        enabled,
      },
    ],
  })
  return {
    services: services.data?.total ?? null,
    assignments: assignments.data?.total ?? null,
    contracts: contracts.data?.total ?? null,
  }
}

export function formatKpi(value: number | null): string {
  if (value === null) return "-"
  if (value < 1000) return value.toString()
  if (value < 10_000) return (value / 1000).toFixed(1).replace(/\.0$/, "") + "k"
  return Math.round(value / 1000) + "k"
}

export interface KpiDelta {
  label: string
  direction: "up" | "down"
  tone: "success" | "danger"
}

/** Percentage change against the prior period; null when it cannot be said. */
export function formatDelta(current: number, prior: number): KpiDelta | null {
  if (prior <= 0 || current === prior) return null
  const change = Math.round(((current - prior) / prior) * 100)
  if (change === 0) return null
  return {
    label: `${Math.abs(change)}%`,
    direction: change > 0 ? "up" : "down",
    tone: change > 0 ? "success" : "danger",
  }
}

const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
]

/** "2026-09" → "Sep". Falls back to the raw key on malformed input. */
export function monthLabel(month: string): string {
  const index = Number(month.slice(5, 7)) - 1
  return MONTH_NAMES[index] ?? month
}

/** "2026-09" → "Sep 2026". */
export function monthLabelLong(month: string): string {
  return `${monthLabel(month)} ${month.slice(0, 4)}`
}

/** Clean axis ticks from zero to above the series maximum, so bars keep headroom. */
export function niceTicks(max: number): number[] {
  if (max <= 0) return [0, 1]
  const rough = Math.max(max / 3, 1)
  const power = 10 ** Math.floor(Math.log10(rough))
  const step = [1, 2, 5, 10].map((s) => s * power).find((s) => s * 4 >= max) ?? power * 10
  const ticks = [0]
  while (ticks[ticks.length - 1] <= max) ticks.push(ticks[ticks.length - 1] + step)
  return ticks
}

export function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ""
  const diff = Date.now() - then
  if (diff < 0) return "just now"
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return "just now"
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const day = Math.floor(hr / 24)
  if (day === 1) return "Yesterday"
  if (day < 7) return `${day}d ago`
  if (day < 30) return `${Math.floor(day / 7)}w ago`
  if (day < 365) return `${Math.floor(day / 30)}mo ago`
  return `${Math.floor(day / 365)}y ago`
}
