/**
 * Dashboard data hooks. Fan-out to existing list endpoints with limit=1 to
 * read the `total` count, since there is no aggregate /dashboard endpoint yet.
 */

import { useQueries } from '@tanstack/react-query'

import { clientsApi } from '@/api/endpoints/clients'
import { contractsApi } from '@/api/endpoints/contracts'
import { incidentsApi } from '@/api/endpoints/incidents'
import { serviceSessionsApi } from '@/api/endpoints/service-sessions'

import { entityListKey } from './queries'

interface KpiResult {
  value: number | null
  loading: boolean
  error: boolean
}

const KPI_PARAMS = { page: 1, limit: 1 } as const
const ONE_MINUTE = 60_000

export function useDashboardKpis() {
  const queries = useQueries({
    queries: [
      {
        queryKey: entityListKey('clients', KPI_PARAMS),
        queryFn: () => clientsApi.list(KPI_PARAMS),
        staleTime: ONE_MINUTE,
      },
      {
        queryKey: entityListKey('incidents', KPI_PARAMS),
        queryFn: () => incidentsApi.list(),
        staleTime: ONE_MINUTE,
      },
      {
        queryKey: entityListKey('service-sessions', KPI_PARAMS),
        queryFn: () => serviceSessionsApi.list(KPI_PARAMS),
        staleTime: ONE_MINUTE,
      },
      {
        queryKey: entityListKey('contracts', KPI_PARAMS),
        queryFn: () => contractsApi.list(KPI_PARAMS),
        staleTime: ONE_MINUTE,
      },
    ],
  })

  const [clients, incidents, sessions, contracts] = queries

  return {
    clients: toResult(clients),
    incidents: toResult(incidents),
    sessions: toResult(sessions),
    contracts: toResult(contracts),
    isLoading: queries.some((q) => q.isLoading),
    isError: queries.every((q) => q.isError),
  }
}

function toResult(q: {
  data?: { total?: number }
  isLoading: boolean
  isError: boolean
}): KpiResult {
  return {
    value: q.data?.total ?? null,
    loading: q.isLoading,
    error: q.isError,
  }
}

export function formatKpi(value: number | null): string {
  if (value === null) return "—"
  if (value < 1000) return value.toString()
  if (value < 10_000) return (value / 1000).toFixed(1).replace(/\.0$/, "") + "k"
  return Math.round(value / 1000) + "k"
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
