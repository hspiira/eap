/**
 * Dashboard data hooks and formatting helpers.
 *
 * One aggregate query feeds the whole page. The onboarding checklist still
 * fans out to three list endpoints, but only for a tenant with no clients,
 * so a working tenant pays for exactly one request.
 */

import { keepPreviousData, useQueries, useQuery } from "@tanstack/react-query"

import { contractsApi } from "@/api/endpoints/contracts"
import { dashboardApi } from "@/api/endpoints/dashboard"
import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { servicesApi } from "@/api/endpoints/services"

import { entityListKey } from "./queries"

const KPI_PARAMS = { page: 1, limit: 1 } as const
const ONE_MINUTE = 60_000

export type RangePreset =
  | "this_week"
  | "this_month"
  | "last_30d"
  | "last_90d"
  | "last_180d"
  | "custom"

export interface DashboardRange {
  preset: RangePreset
  start?: string
  end?: string
}

export const DEFAULT_RANGE: DashboardRange = { preset: "last_90d" }

const RANGE_LABELS: Record<RangePreset, string> = {
  this_week: "this week",
  this_month: "this month",
  last_30d: "last 30 days",
  last_90d: "last 90 days",
  last_180d: "last 6 months",
  custom: "selected range",
}

export function rangeLabel(range: DashboardRange): string {
  return RANGE_LABELS[range.preset]
}

/**
 * Holds the previous render while a new window loads, so switching range
 * dims the charts rather than collapsing the page into skeletons.
 */
export function useDashboard(range: DashboardRange) {
  return useQuery({
    queryKey: ["dashboard", "aggregate", range],
    queryFn: () => dashboardApi.get(range),
    staleTime: ONE_MINUTE,
    placeholderData: keepPreviousData,
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
